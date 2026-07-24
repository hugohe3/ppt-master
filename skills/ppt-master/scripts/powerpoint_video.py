#!/usr/bin/env python3
"""
PPT Master - PowerPoint Video Export

Export a narrated PPTX through the installed Windows PowerPoint application and
wait until its native video encoder finishes.

See workflows/stages/generate-audio.md for the narration handoff.

Usage:
    python3 scripts/powerpoint_video.py <pptx> [-o <video>]
    python3 scripts/powerpoint_video.py --check

Examples:
    python3 scripts/powerpoint_video.py projects/demo/exports/demo_narrated.pptx
    python3 scripts/powerpoint_video.py deck.pptx -o deck.mp4 --resolution 1080

Dependencies:
    Windows PowerPoint with the CreateVideo automation API
"""

from __future__ import annotations

import argparse
import base64
import os
import shutil
import subprocess
import sys
from pathlib import Path

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()


_CHECK_SCRIPT = r"""
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$powerPoint = $null
$ownsApplication = $false

try {
    try {
        $powerPoint = [Runtime.InteropServices.Marshal]::GetActiveObject(
            "PowerPoint.Application"
        )
    }
    catch {
        $powerPoint = New-Object -ComObject PowerPoint.Application
        $ownsApplication = $true
    }

    $version = [version]$powerPoint.Version
    if ($version.Major -lt 16) {
        throw "PowerPoint $version is older than the supported Office 2016 baseline."
    }
    [Console]::Out.WriteLine(
        "PowerPoint video export available (version {0})." -f $version
    )
}
catch {
    [Console]::Error.WriteLine(
        "PowerPoint video export is unavailable: {0}" -f $_.Exception.Message
    )
    exit 1
}
finally {
    if ($null -ne $powerPoint) {
        if ($ownsApplication) {
            try { $powerPoint.Quit() } catch {}
        }
        try {
            [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject(
                $powerPoint
            )
        }
        catch {}
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
"""


_EXPORT_SCRIPT = r"""
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$inputPath = [Environment]::GetEnvironmentVariable("PPT_MASTER_VIDEO_INPUT")
$outputPath = [Environment]::GetEnvironmentVariable("PPT_MASTER_VIDEO_OUTPUT")
$resolution = [int][Environment]::GetEnvironmentVariable(
    "PPT_MASTER_VIDEO_RESOLUTION"
)
$framesPerSecond = [int][Environment]::GetEnvironmentVariable(
    "PPT_MASTER_VIDEO_FPS"
)
$quality = [int][Environment]::GetEnvironmentVariable("PPT_MASTER_VIDEO_QUALITY")
$defaultSlideDuration = [int][Environment]::GetEnvironmentVariable(
    "PPT_MASTER_VIDEO_DEFAULT_SLIDE_DURATION"
)
$timeoutSeconds = [int][Environment]::GetEnvironmentVariable(
    "PPT_MASTER_VIDEO_TIMEOUT"
)

$powerPoint = $null
$presentation = $null
$ownsApplication = $false

try {
    try {
        $powerPoint = [Runtime.InteropServices.Marshal]::GetActiveObject(
            "PowerPoint.Application"
        )
    }
    catch {
        $powerPoint = New-Object -ComObject PowerPoint.Application
        $ownsApplication = $true
    }

    $version = [version]$powerPoint.Version
    if ($version.Major -lt 16) {
        throw "PowerPoint $version is older than the supported Office 2016 baseline."
    }

    # ReadOnly=-1, Untitled=0, WithWindow=0.
    $presentation = $powerPoint.Presentations.Open($inputPath, -1, 0, 0)
    $startMessage = "PowerPoint video export started: {0}p, {1} fps." -f @(
        $resolution,
        $framesPerSecond
    )
    [Console]::Error.WriteLine($startMessage)
    $presentation.CreateVideo(
        $outputPath,
        $true,
        $defaultSlideDuration,
        $resolution,
        $framesPerSecond,
        $quality
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($timeoutSeconds)
    $nextProgress = [DateTime]::UtcNow.AddSeconds(15)
    while ($true) {
        $status = [int]$presentation.CreateVideoStatus
        if ($status -eq 3) {
            break
        }
        if ($status -eq 4) {
            throw "PowerPoint reported that video creation failed."
        }
        if ([DateTime]::UtcNow -ge $deadline) {
            throw "PowerPoint video creation exceeded the ${timeoutSeconds}-second timeout."
        }
        if ([DateTime]::UtcNow -ge $nextProgress) {
            [Console]::Error.WriteLine("PowerPoint video export is still running.")
            $nextProgress = [DateTime]::UtcNow.AddSeconds(15)
        }
        Start-Sleep -Milliseconds 1000
    }

    if (-not (Test-Path -LiteralPath $outputPath)) {
        throw "PowerPoint reported success but did not create the output file."
    }
    $outputFile = Get-Item -LiteralPath $outputPath
    if ($outputFile.Length -le 0) {
        throw "PowerPoint created an empty video file."
    }

    [Console]::Out.WriteLine($outputFile.FullName)
}
catch {
    $errorMessage = (
        "PowerPoint video export failed: {0} " +
        "Close any PowerPoint dialog and retry."
    ) -f $_.Exception.Message
    [Console]::Error.WriteLine($errorMessage)
    exit 1
}
finally {
    if ($null -ne $presentation) {
        try { $presentation.Close() } catch {}
        try {
            [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject(
                $presentation
            )
        }
        catch {}
    }
    if ($null -ne $powerPoint) {
        if ($ownsApplication) {
            try { $powerPoint.Quit() } catch {}
        }
        try {
            [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject(
                $powerPoint
            )
        }
        catch {}
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export a PPTX with Windows PowerPoint's native video encoder and "
            "wait for completion."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("pptx", nargs="?", help="Input PPTX file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Output .mp4 or .wmv path. Default: beside the PPTX as .mp4.",
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=1080,
        help="Vertical video resolution in pixels (default: 1080).",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Frames per second, from 1 to 60 (default: 30).",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=85,
        help="PowerPoint encoder quality, from 1 to 100 (default: 85).",
    )
    parser.add_argument(
        "--default-slide-duration",
        type=int,
        default=5,
        help="Fallback seconds for slides without recorded timings (default: 5).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=7200,
        help="Maximum seconds to wait for PowerPoint (default: 7200).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing output video.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check whether compatible Windows PowerPoint automation is available.",
    )
    return parser


def _find_powershell() -> str | None:
    """Return the local Windows PowerShell executable."""
    return shutil.which("powershell.exe") or shutil.which("powershell")


def _run_powershell(script: str, *, env: dict[str, str], timeout: int) -> int:
    """Run an encoded PowerShell automation script."""
    executable = _find_powershell()
    if executable is None:
        print(
            "PowerPoint video export requires Windows PowerShell. "
            "Install or restore powershell.exe, then retry.",
            file=sys.stderr,
        )
        return 1

    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    try:
        completed = subprocess.run(
            [
                executable,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-STA",
                "-OutputFormat",
                "Text",
                "-EncodedCommand",
                encoded,
            ],
            check=False,
            env=env,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        print(
            "PowerPoint automation exceeded the command timeout. "
            "Close any PowerPoint dialog and retry.",
            file=sys.stderr,
        )
        return 1
    return completed.returncode


def _validate_positive(
    parser: argparse.ArgumentParser,
    *,
    name: str,
    value: int,
    maximum: int | None = None,
) -> None:
    if value <= 0 or (maximum is not None and value > maximum):
        suffix = f" and no greater than {maximum}" if maximum is not None else ""
        parser.error(f"{name} must be greater than 0{suffix}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if sys.platform != "win32":
        print(
            "PowerPoint video export currently requires Windows PowerPoint. "
            "Keep the narrated PPTX and export it manually on another platform.",
            file=sys.stderr,
        )
        return 1

    if args.check:
        return _run_powershell(
            _CHECK_SCRIPT,
            env=os.environ.copy(),
            timeout=60,
        )

    if not args.pptx:
        parser.error("pptx is required unless --check is used")

    _validate_positive(parser, name="resolution", value=args.resolution)
    _validate_positive(parser, name="fps", value=args.fps, maximum=60)
    _validate_positive(parser, name="quality", value=args.quality, maximum=100)
    _validate_positive(
        parser,
        name="default-slide-duration",
        value=args.default_slide_duration,
    )
    _validate_positive(parser, name="timeout", value=args.timeout)

    input_path = Path(args.pptx).expanduser().resolve()
    if not input_path.is_file():
        print(f"Input PPTX does not exist: {input_path}", file=sys.stderr)
        return 1
    if input_path.suffix.lower() != ".pptx":
        print(f"Input must be a .pptx file: {input_path}", file=sys.stderr)
        return 1

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else input_path.with_suffix(".mp4")
    )
    if output_path.suffix.lower() not in {".mp4", ".wmv"}:
        print(
            f"Output must use the .mp4 or .wmv extension: {output_path}",
            file=sys.stderr,
        )
        return 1
    if output_path == input_path:
        print("Input PPTX and output video paths must differ.", file=sys.stderr)
        return 1
    if output_path.exists() and not args.force:
        print(
            f"Output already exists: {output_path}. "
            "Use --force to replace it.",
            file=sys.stderr,
        )
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    env = os.environ.copy()
    env.update(
        {
            "PPT_MASTER_VIDEO_INPUT": str(input_path),
            "PPT_MASTER_VIDEO_OUTPUT": str(output_path),
            "PPT_MASTER_VIDEO_RESOLUTION": str(args.resolution),
            "PPT_MASTER_VIDEO_FPS": str(args.fps),
            "PPT_MASTER_VIDEO_QUALITY": str(args.quality),
            "PPT_MASTER_VIDEO_DEFAULT_SLIDE_DURATION": str(
                args.default_slide_duration
            ),
            "PPT_MASTER_VIDEO_TIMEOUT": str(args.timeout),
        }
    )
    return _run_powershell(
        _EXPORT_SCRIPT,
        env=env,
        timeout=args.timeout + 60,
    )


if __name__ == "__main__":
    raise SystemExit(main())
