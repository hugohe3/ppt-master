#!/usr/bin/env python3
"""
PPT Master - SVG Editor Server

Flask backend for the SVG annotation editor.
Serves the web UI and provides API endpoints for reading/writing SVG annotations.

Usage:
    python3 scripts/svg_editor/server.py <project_dir>

Examples:
    python3 scripts/svg_editor/server.py projects/my-project
    python3 scripts/svg_editor/server.py projects/my-project --port 8080

Dependencies:
    flask>=3.0.0
"""

import argparse
import sys
import webbrowser
import xml.etree.ElementTree as ET
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from .annotations import (
    assign_temp_ids,
    parse_annotations,
    set_annotation,
    remove_annotation,
)


def create_app(project_dir: str) -> Flask:
    """
    Create and configure the Flask app.

    Args:
        project_dir: Path to the ppt-master project directory (contains svg_output/).
    """
    project_path = Path(project_dir).resolve()
    svg_dir = project_path / 'svg_output'

    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config['PROJECT_PATH'] = project_path
    app.config['SVG_DIR'] = svg_dir

    # In-memory annotation store: {filename: {element_id: annotation_text}}
    app.config['ANNOTATIONS'] = {}

    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/api/slides')
    def get_slides():
        svg_dir = app.config['SVG_DIR']
        if not svg_dir.exists():
            return jsonify({'slides': []})

        annotations = app.config['ANNOTATIONS']
        slides = []
        for svg_file in sorted(svg_dir.glob('*.svg')):
            has_disk_anns = False
            try:
                tree = ET.parse(str(svg_file))
                for elem in tree.getroot().iter():
                    if elem.get('data-edit-target') == 'true':
                        has_disk_anns = True
                        break
            except ET.ParseError:
                pass

            has_mem_anns = svg_file.name in annotations and len(annotations[svg_file.name]) > 0

            slides.append({
                'name': svg_file.name,
                'annotated': has_disk_anns or has_mem_anns,
                'annotation_count': len(annotations.get(svg_file.name, {})),
            })

        return jsonify({'slides': slides})

    @app.route('/api/slide/<name>')
    def get_slide(name: str):
        svg_file = app.config['SVG_DIR'] / name
        if not svg_file.exists():
            return jsonify({'error': 'Slide not found'}), 404

        try:
            tree = ET.parse(str(svg_file))
            root = tree.getroot()
        except ET.ParseError as e:
            return jsonify({'error': f'Failed to parse SVG: {e}'}), 500

        assign_temp_ids(root)

        disk_annotations = parse_annotations(root)

        mem_annotations = app.config['ANNOTATIONS'].get(name, {})
        merged = {}
        for ann in disk_annotations:
            merged[ann['element_id']] = ann['annotation']
        merged.update(mem_annotations)

        annotations_list = []
        for elem in root.iter():
            eid = elem.get('id')
            if eid and eid in merged:
                tag = elem.tag
                if '}' in tag:
                    tag = tag.split('}', 1)[1]
                annotations_list.append({
                    'element_id': eid,
                    'tag': tag,
                    'annotation': merged[eid],
                })

        content = ET.tostring(root, encoding='unicode', xml_declaration=False)

        return jsonify({
            'name': name,
            'content': content,
            'annotations': annotations_list,
        })

    @app.route('/api/slide/<name>/annotate', methods=['POST'])
    def post_annotate(name: str):
        data = request.get_json()
        if not data or 'element_id' not in data or 'annotation' not in data:
            return jsonify({'error': 'Missing element_id or annotation'}), 400

        element_id = data['element_id']
        annotation = data['annotation']

        if name not in app.config['ANNOTATIONS']:
            app.config['ANNOTATIONS'][name] = {}

        app.config['ANNOTATIONS'][name][element_id] = annotation

        return jsonify({
            'status': 'ok',
            'annotations_count': len(app.config['ANNOTATIONS'][name]),
        })

    @app.route('/api/slide/<name>/annotate/<element_id>', methods=['DELETE'])
    def delete_annotate(name: str, element_id: str):
        annotations = app.config['ANNOTATIONS']
        if name in annotations and element_id in annotations[name]:
            del annotations[name][element_id]

        return jsonify({
            'status': 'ok',
            'annotations_count': len(annotations.get(name, {})),
        })

    @app.route('/api/save-all', methods=['POST'])
    def save_all():
        annotations = app.config['ANNOTATIONS']
        svg_dir = app.config['SVG_DIR']
        modified = []

        for filename, anns in annotations.items():
            if not anns:
                continue

            svg_file = svg_dir / filename
            if not svg_file.exists():
                continue

            try:
                tree = ET.parse(str(svg_file))
                root = tree.getroot()
            except ET.ParseError:
                continue

            for element_id, annotation_text in anns.items():
                set_annotation(root, element_id, annotation_text)

            tree.write(str(svg_file), encoding='unicode', xml_declaration=True)
            modified.append(filename)

        app.config['ANNOTATIONS'] = {}

        return jsonify({'status': 'ok', 'files_modified': modified})

    return app


def main():
    parser = argparse.ArgumentParser(
        description='PPT Master SVG Editor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 scripts/svg_editor/server.py projects/my-project
    python3 scripts/svg_editor/server.py projects/my-project --port 8080
        """
    )
    parser.add_argument('project_dir', help='Path to project directory (contains svg_output/)')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on (default: 5000)')
    parser.add_argument('--no-browser', action='store_true', help='Do not auto-open browser')
    args = parser.parse_args()

    project_path = Path(args.project_dir).resolve()
    if not (project_path / 'svg_output').exists():
        print(f"Error: {project_path / 'svg_output'} does not exist", file=sys.stderr)
        sys.exit(1)

    app = create_app(str(project_path))

    url = f'http://localhost:{args.port}'
    if not args.no_browser:
        webbrowser.open(url)

    print(f"SVG Editor running at {url}")
    print(f"Project: {project_path}")
    app.run(host='127.0.0.1', port=args.port, debug=False)


if __name__ == '__main__':
    main()
