#!/usr/bin/env node
/**
 * web_to_md.cjs - Web Page to Markdown Converter (Enhanced)
 *
 * Usage:
 *   node tools/web_to_md.cjs <url>              # Single URL
 *   node tools/web_to_md.cjs <url1> <url2> ...  # Multiple URLs
 *   node tools/web_to_md.cjs -f urls.txt        # Read URLs from file
 *   node tools/web_to_md.cjs <url> -o output.md # Specify output filename
 */

const fs = require("fs").promises;
const path = require("path");
const https = require("https");
const http = require("http");

// ============ Config ============
const CONFIG = {
  outputDir: "./projects",
  timeout: 30000,
  userAgent:
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
};

// ============ HTTP Fetch with encoding detection ============
async function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith("https") ? https : http;
    const options = {
      headers: {
        "User-Agent": CONFIG.userAgent,
        Accept:
          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
      },
      timeout: CONFIG.timeout,
    };

    const req = client.get(url, options, (res) => {
      // Handle redirects
      if (
        res.statusCode >= 300 &&
        res.statusCode < 400 &&
        res.headers.location
      ) {
        const redirectUrl = new URL(res.headers.location, url).href;
        return fetchUrl(redirectUrl).then(resolve).catch(reject);
      }

      if (res.statusCode !== 200) {
        reject(new Error("HTTP " + res.statusCode));
        return;
      }

      const chunks = [];
      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => {
        const buffer = Buffer.concat(chunks);

        // Detect encoding from Content-Type header or meta tag
        let encoding = "utf-8";
        const contentType = res.headers["content-type"] || "";
        const charsetMatch = contentType.match(/charset=([^;]+)/i);
        if (charsetMatch) {
          encoding = charsetMatch[1].trim().toLowerCase();
        }

        // Try UTF-8 first, then check for charset in HTML
        let html = buffer.toString("utf-8");

        // Check for meta charset in HTML
        const metaCharsetMatch = html.match(
          /<meta[^>]*charset=["']?([^"'\s>]+)/i
        );
        if (metaCharsetMatch) {
          const declaredEncoding = metaCharsetMatch[1].toLowerCase();
          if (
            declaredEncoding === "gbk" ||
            declaredEncoding === "gb2312" ||
            declaredEncoding === "gb18030"
          ) {
            // For Chinese GBK encoding, we'd need iconv-lite
            // For now, UTF-8 usually works for modern sites
          }
        }

        resolve(html);
      });
    });

    req.on("error", reject);
    req.on("timeout", () => {
      req.destroy();
      reject(new Error("Request timeout"));
    });
  });
}

// ============ Enhanced HTML Parser ============
function parseHTML(html) {
  // Extract title
  const titleMatch = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  let title = titleMatch ? decodeHTMLEntities(titleMatch[1].trim()) : "";
  // Clean title - remove site name suffix
  title = title.replace(/[-_|].*?(政府|门户|网站|委员会).*$/g, "").trim();

  // Extract meta tags
  const metas = {};
  const metaRegex = /<meta[^>]+>/gi;
  let metaMatch;
  while ((metaMatch = metaRegex.exec(html)) !== null) {
    const tag = metaMatch[0];
    const nameMatch = tag.match(/(?:name|property)=["']([^"']+)["']/i);
    const contentMatch = tag.match(/content=["']([^"']+)["']/i);
    if (nameMatch && contentMatch) {
      metas[nameMatch[1].toLowerCase()] = decodeHTMLEntities(contentMatch[1]);
    }
  }

  // Enhanced content extraction - try multiple strategies
  let content = extractMainContent(html);

  return { title, metas, content };
}

// ============ Enhanced Main Content Extraction ============
function extractMainContent(html) {
  // Remove unwanted elements first
  let cleanHtml = html;

  // Remove script, style, nav, header, footer, sidebar, comments
  cleanHtml = cleanHtml.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, "");
  cleanHtml = cleanHtml.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, "");
  cleanHtml = cleanHtml.replace(/<nav[^>]*>[\s\S]*?<\/nav>/gi, "");
  cleanHtml = cleanHtml.replace(/<header[^>]*>[\s\S]*?<\/header>/gi, "");
  cleanHtml = cleanHtml.replace(/<footer[^>]*>[\s\S]*?<\/footer>/gi, "");
  cleanHtml = cleanHtml.replace(/<aside[^>]*>[\s\S]*?<\/aside>/gi, "");
  cleanHtml = cleanHtml.replace(/<!--[\s\S]*?-->/g, "");

  // Common content container patterns for Chinese government websites
  const contentPatterns = [
    // WeChat Public Account
    /<div[^>]*class=["'][^"']*rich_media_content[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*id=["']js_content["'][^>]*>([\s\S]*?)<\/div>/i,
    // Hunan province gov sites
    /<div[^>]*class=["'][^"']*tys-main-zt-show[^"']*["'][^>]?>([\s\S]*?)<\/div>\s*<\/div>\s*<\/div>/i,
    /<div[^>]*class=["'][^"']*tys-main-zt-show[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*class=["'][^"']*tys-main[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    // Exact class matches for government sites
    /<div[^>]*class=["'][^"']*TRS_Editor[^"']*["'][^>]*>([\s\S]*?)<\/div>\s*(?:<\/div>)?/i,
    /<div[^>]*class=["'][^"']*TRS_UEDITOR[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*class=["'][^"']*ucontent[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*class=["'][^"']*article-content[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*class=["'][^"']*news-content[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*class=["'][^"']*detail-content[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*class=["'][^"']*content-text[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*class=["'][^"']*pages_content[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*class=["'][^"']*zwgk_content[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*class=["'][^"']*content_detail[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*class=["'][^"']*text_content[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*class=["'][^"']*main-content[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*class=["'][^"']*main_content[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*class=["'][^"']*view-content[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*class=["'][^"']*info-content[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*id=["']?Zoom["']?[^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*id=["']?content["']?[^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*id=["']?article["']?[^>]*>([\s\S]*?)<\/div>/i,
    // ID-based patterns
    /<div[^>]*id=["'][^"']*content[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    /<div[^>]*id=["'][^"']*article[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
    // Standard semantic elements
    /<article[^>]*>([\s\S]*?)<\/article>/i,
    /<main[^>]*>([\s\S]*?)<\/main>/i,
    // Generic content divs (less specific)
    /<div[^>]*class=["'][^"']*content[^"']*["'][^>]*>([\s\S]*?)<\/div>/i,
  ];

  // Try each pattern and find the one with most text content
  let bestContent = "";
  let bestTextLength = 0;

  for (const pattern of contentPatterns) {
    // Use a greedy matching approach for nested divs
    const matches = findAllMatches(cleanHtml, pattern);
    for (const match of matches) {
      const textContent = stripTags(match).trim();
      // Prefer content with Chinese characters (for gov sites)
      const chineseChars = (textContent.match(/[\u4e00-\u9fa5]/g) || []).length;
      const score = textContent.length + chineseChars * 2;
      if (score > bestTextLength && textContent.length > 200) {
        bestContent = match;
        bestTextLength = score;
      }
    }
  }

  // If still not found, try to find content between common markers
  if (!bestContent || bestTextLength < 500) {
    // Look for content area by finding dense paragraph areas
    const bodyMatch = cleanHtml.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
    if (bodyMatch) {
      const bodyContent = bodyMatch[1];
      // Find the area with most <p> tags
      const areas = bodyContent.split(/<div[^>]*>/i);
      for (const area of areas) {
        const pCount = (area.match(/<p[^>]*>/gi) || []).length;
        const textLen = stripTags(area).length;
        if (pCount >= 2 && textLen > bestTextLength) {
          bestContent = area;
          bestTextLength = textLen;
        }
      }
    }
  }

  // Fallback to body
  if (!bestContent) {
    const bodyMatch = cleanHtml.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
    bestContent = bodyMatch ? bodyMatch[1] : cleanHtml;
  }

  return bestContent;
}

// Helper function to find all regex matches
function findAllMatches(html, pattern) {
  const results = [];
  const globalPattern = new RegExp(pattern.source, "gi");
  let match;
  while ((match = globalPattern.exec(html)) !== null) {
    if (match[1]) {
      results.push(match[1]);
    }
  }
  return results;
}

// Helper function to strip HTML tags for text length calculation
function stripTags(html) {
  return html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ");
}

// ============ HTML Entity Decoder ============
function decodeHTMLEntities(str) {
  const entities = {
    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": '"',
    "&#39;": "'",
    "&nbsp;": " ",
    "&mdash;": "\u2014",
    "&ndash;": "\u2013",
    "&copy;": "\u00A9",
    "&reg;": "\u00AE",
    "&trade;": "\u2122",
    "&hellip;": "\u2026",
    "&ldquo;": "\u201C",
    "&rdquo;": "\u201D",
    "&lsquo;": "\u2018",
    "&rsquo;": "\u2019",
    "&ensp;": " ",
    "&emsp;": "  ",
    "&middot;": "\u00B7",
    "&bull;": "\u2022",
    "&times;": "\u00D7",
    "&divide;": "\u00F7",
    "&plusmn;": "\u00B1",
    "&laquo;": "\u00AB",
    "&raquo;": "\u00BB",
  };
  // Handle numeric entities
  str = str.replace(/&#(\d+);/g, function (match, dec) {
    return String.fromCharCode(dec);
  });
  str = str.replace(/&#x([0-9a-fA-F]+);/g, function (match, hex) {
    return String.fromCharCode(parseInt(hex, 16));
  });
  // Handle named entities
  return str.replace(/&[a-zA-Z]+;/g, function (match) {
    return entities[match] || match;
  });
}

// ============ Enhanced HTML to Markdown Converter ============
function htmlToMarkdown(html) {
  let md = html;

  // First pass: remove unwanted elements
  md = md.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, "");
  md = md.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, "");
  md = md.replace(/<nav[^>]*>[\s\S]*?<\/nav>/gi, "");
  md = md.replace(/<header[^>]*>[\s\S]*?<\/header>/gi, "");
  md = md.replace(/<footer[^>]*>[\s\S]*?<\/footer>/gi, "");
  md = md.replace(/<!--[\s\S]*?-->/g, "");

  // Convert headings
  md = md.replace(/<h1[^>]*>([\s\S]*?)<\/h1>/gi, "\n# $1\n");
  md = md.replace(/<h2[^>]*>([\s\S]*?)<\/h2>/gi, "\n## $1\n");
  md = md.replace(/<h3[^>]*>([\s\S]*?)<\/h3>/gi, "\n### $1\n");
  md = md.replace(/<h4[^>]*>([\s\S]*?)<\/h4>/gi, "\n#### $1\n");
  md = md.replace(/<h5[^>]*>([\s\S]*?)<\/h5>/gi, "\n##### $1\n");
  md = md.replace(/<h6[^>]*>([\s\S]*?)<\/h6>/gi, "\n###### $1\n");

  // Convert paragraphs
  md = md.replace(/<p[^>]*>([\s\S]*?)<\/p>/gi, "\n$1\n");
  md = md.replace(/<div[^>]*>([\s\S]*?)<\/div>/gi, "\n$1\n");
  md = md.replace(/<br\s*\/?>/gi, "\n");
  md = md.replace(/<hr\s*\/?>/gi, "\n---\n");

  // Convert text formatting
  md = md.replace(/<(strong|b)[^>]*>([\s\S]*?)<\/\1>/gi, "**$2**");
  md = md.replace(/<(em|i)[^>]*>([\s\S]*?)<\/\1>/gi, "*$2*");
  md = md.replace(/<u[^>]*>([\s\S]*?)<\/u>/gi, "$1");
  md = md.replace(/<del[^>]*>([\s\S]*?)<\/del>/gi, "~~$1~~");
  md = md.replace(/<s[^>]*>([\s\S]*?)<\/s>/gi, "~~$1~~");
  md = md.replace(/<span[^>]*>([\s\S]*?)<\/span>/gi, "$1");

  // Convert links - handle nested content properly
  md = md.replace(
    /<a[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,
    function (match, url, text) {
      const cleanText = text.replace(/<[^>]+>/g, "").trim();
      if (!cleanText || url.startsWith("javascript:")) {
        return cleanText;
      }
      return "[" + cleanText + "](" + url + ")";
    }
  );

  // Convert images
  md = md.replace(
    /<img[^>]*src=["']([^"']+)["'][^>]*alt=["']([^"']*)["'][^>]*\/?>/gi,
    "![$2]($1)"
  );
  md = md.replace(
    /<img[^>]*alt=["']([^"']*)["'][^>]*src=["']([^"']+)["'][^>]*\/?>/gi,
    "![$1]($2)"
  );
  md = md.replace(/<img[^>]*src=["']([^"']+)["'][^>]*\/?>/gi, "![]($1)");

  // Convert lists
  md = md.replace(/<li[^>]*>([\s\S]*?)<\/li>/gi, function (match, content) {
    const cleanContent = content.replace(/<[^>]+>/g, "").trim();
    return "- " + cleanContent + "\n";
  });
  md = md.replace(/<\/?[uo]l[^>]*>/gi, "\n");

  // Convert code
  md = md.replace(/<code[^>]*>([\s\S]*?)<\/code>/gi, "`$1`");
  md = md.replace(/<pre[^>]*>([\s\S]*?)<\/pre>/gi, "\n```\n$1\n```\n");

  // Convert blockquotes
  md = md.replace(
    /<blockquote[^>]*>([\s\S]*?)<\/blockquote>/gi,
    function (match, content) {
      const lines = content.replace(/<[^>]+>/g, "").split("\n");
      return (
        "\n" +
        lines
          .map(function (line) {
            return "> " + line.trim();
          })
          .filter(function (l) {
            return l.trim() !== ">";
          })
          .join("\n") +
        "\n"
      );
    }
  );

  // Convert tables
  md = md.replace(
    /<table[^>]*>([\s\S]*?)<\/table>/gi,
    function (match, content) {
      let result = "\n";
      const rows = content.match(/<tr[^>]*>[\s\S]*?<\/tr>/gi) || [];
      rows.forEach(function (row, index) {
        const cells = row.match(/<t[hd][^>]*>([\s\S]*?)<\/t[hd]>/gi) || [];
        const cellContents = cells.map(function (cell) {
          const cellMatch = cell.match(/<t[hd][^>]*>([\s\S]*?)<\/t[hd]>/i);
          return cellMatch ? cellMatch[1].replace(/<[^>]+>/g, "").trim() : "";
        });
        if (cellContents.length > 0) {
          result += "| " + cellContents.join(" | ") + " |\n";
          if (index === 0) {
            result +=
              "| " +
              cellContents
                .map(function () {
                  return "---";
                })
                .join(" | ") +
              " |\n";
          }
        }
      });
      return result;
    }
  );

  // Clean remaining HTML tags
  md = md.replace(/<[^>]+>/g, "");

  // Decode HTML entities
  md = decodeHTMLEntities(md);

  // Clean up whitespace
  md = md.replace(/\r\n/g, "\n");
  md = md.replace(/\n{3,}/g, "\n\n");
  md = md.replace(/[ \t]+$/gm, "");
  md = md.replace(/^[ \t]+/gm, "");

  // Remove lines that are just whitespace or single characters
  md = md
    .split("\n")
    .filter(function (line) {
      const trimmed = line.trim();
      return trimmed.length > 1 || trimmed === "" || /^[-#>*|]/.test(trimmed);
    })
    .join("\n");

  md = md.trim();

  return md;
}

// ============ Extract Metadata ============
function extractMetadata(parsed, url) {
  const title = parsed.title;
  const metas = parsed.metas;

  // Try to extract date from multiple sources
  let date =
    metas["article:published_time"] ||
    metas["og:published_time"] ||
    metas["pubdate"] ||
    metas["publishdate"] ||
    metas["date"] ||
    "";

  // Try to extract date from HTML content
  if (!date) {
    const content = parsed.content;
    // Common date patterns in Chinese gov sites
    const datePatterns = [
      /发布[时日]间[：:]\s*(\d{4}[-\/年]\d{1,2}[-\/月]\d{1,2}[日]?)/,
      /日期[：:]\s*(\d{4}[-\/年]\d{1,2}[-\/月]\d{1,2}[日]?)/,
      /(\d{4}[-\/年]\d{1,2}[-\/月]\d{1,2}[日]?)\s*(?:发布|来源)/,
      /时间[：:]\s*(\d{4}[-\/]\d{1,2}[-\/]\d{1,2})/,
    ];
    for (const pattern of datePatterns) {
      const match = content.match(pattern);
      if (match) {
        date = match[1].replace(/[年月]/g, "-").replace(/[日]/g, "");
        break;
      }
    }
  }

  // Try to extract date from URL
  if (!date) {
    const urlDateMatch = url.match(/(\d{4})(\d{2})[\/_](?:t\d+_)?/i);
    if (urlDateMatch) {
      date = urlDateMatch[1] + "-" + urlDateMatch[2];
    } else {
      const urlDateMatch2 = url.match(/(\d{4})[-\/](\d{2})[-\/](\d{2})/);
      if (urlDateMatch2) {
        date =
          urlDateMatch2[1] + "-" + urlDateMatch2[2] + "-" + urlDateMatch2[3];
      }
    }
  }

  const description =
    metas["description"] ||
    metas["og:description"] ||
    metas["twitter:description"] ||
    "";

  const author = metas["author"] || metas["article:author"] || "";

  const keywords = metas["keywords"] || "";

  // Extract source/publisher from content
  let source = "";
  const sourcePatterns = [
    /来源[：:]\s*([^\s<]+)/,
    /发布(?:单位|机构)[：:]\s*([^\s<]+)/,
  ];
  for (const pattern of sourcePatterns) {
    const match = parsed.content.match(pattern);
    if (match) {
      source = match[1];
      break;
    }
  }

  return {
    title: title || metas["og:title"] || "",
    date: date,
    description: description,
    author: author || source,
    keywords: keywords,
    sourceUrl: url,
  };
}

// ============ Sanitize Filename ============
function sanitizeFilename(name) {
  return name
    .replace(/\s+/g, "_")
    .replace(/[^\u4e00-\u9fa5a-zA-Z0-9_]/g, "")
    .replace(/_+/g, "_")
    .substring(0, 80);
}

// ============ Image Downloader & Processor ============
function downloadImage(url, savePath) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith("https") ? https : http;
    const req = client.get(
      url,
      {
        headers: {
          "User-Agent": CONFIG.userAgent,
          Accept: "image/*,*/*",
        },
        timeout: CONFIG.timeout,
      },
      (res) => {
        if (res.statusCode !== 200) {
          res.resume();
          return reject(new Error("Status " + res.statusCode));
        }
        const fileStream = require("fs").createWriteStream(savePath);
        res.pipe(fileStream);
        fileStream.on("finish", () => {
          fileStream.close();
          resolve();
        });
        fileStream.on("error", (err) => {
          reject(err);
        });
      }
    );
    req.on("error", (err) => reject(err));
    req.on("timeout", () => {
      req.destroy();
      reject(new Error("Timeout"));
    });
  });
}

function buildImageFilename(urlStr, index) {
  try {
    const u = new URL(urlStr);
    const basename = path.basename(u.pathname);
    let ext = path.extname(basename);
    let name = path.basename(basename, ext);

    name = sanitizeFilename(name);
    if (!name) name = "image_" + index;
    // Basic extension check
    if (!ext || ext.length > 5 || !/^\.[a-z0-9]+$/i.test(ext)) ext = ".jpg";

    return name + ext;
  } catch (e) {
    return "image_" + index + ".jpg";
  }
}

async function processImages(html, pageUrl, imageDir, relPrefix) {
  const imgRegex = /<img[^>]+src=["']([^"']+)["'][^>]*>/gi;
  const matches = [...html.matchAll(imgRegex)];

  if (matches.length === 0) return html;

  console.log("   [Processing] Found " + matches.length + " images...");

  // Ensure image dir exists
  await fs.mkdir(imageDir, { recursive: true });

  const urlMap = new Map();
  const uniqueUrls = new Set();

  for (const m of matches) {
    if (m[1]) uniqueUrls.add(m[1]);
  }

  let idx = 0;
  for (const src of uniqueUrls) {
    if (src.startsWith("data:") || src.startsWith("#")) continue;

    try {
      // Resolve absolute URL
      const absUrl = new URL(src, pageUrl).href;
      // Generate filename
      const filename = buildImageFilename(absUrl, idx++);

      // Avoid overwriting existing files with same name but different content?
      // For now, simpler collision avoidance
      let saveName = filename;
      let counter = 1;

      // Note: This collision check is basic.
      while (true) {
        try {
          await fs.access(path.join(imageDir, saveName));
          const parsed = path.parse(filename);
          saveName = parsed.name + "_" + counter++ + parsed.ext;
        } catch {
          break; // file does not exist
        }
      }

      const savePath = path.join(imageDir, saveName);
      await downloadImage(absUrl, savePath);

      // Relative path for Markdown
      const relPath = relPrefix
        ? path.join(relPrefix, saveName)
        : saveName;
      
      // Force forward slashes for Markdown compatibility
      urlMap.set(src, relPath.replace(/\\/g, "/"));
    } catch (e) {
      console.log("   [WARN] Image fail " + src + ": " + e.message);
    }
  }

  // Replace src in HTML
  return html.replace(imgRegex, (match, src) => {
    if (urlMap.has(src)) {
      // Replace only the src part of the match
      // Simplest robust way is to replace the exact src string within the match
      // but we must be careful not to replace other attributes' values if identical.
      // A safer way is to reconstruct, but regex is tricky.
      // Current approach: replace the FIRST occurrence of src in the match?
      // No, src is what we extracted.
      
      // Let's replace `src="URL"` with `src="NEW_URL"`?
      // Match structure is roughly `<img ... src="URL" ...>`
      // We can look for `src=["']URL["']` inside `match`.
      
      // Create a regex for this specific src in this tag
      // Escape special regex chars in src
      const escapedSrc = src.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const srcReplaceRegex = new RegExp(`(src=["'])(${escapedSrc})(["'])`, "i");
      return match.replace(srcReplaceRegex, `$1${urlMap.get(src)}$3`);
    }
    return match;
  });
}

// ============ Process Single URL ============
// ============ Process Single URL ============
async function processUrl(url, outputPath) {
  console.log("\n[Fetching] " + url);

  try {
    const html = await fetchUrl(url);
    console.log("   [OK] Fetched (" + (html.length / 1024).toFixed(1) + " KB)");

    const parsed = parseHTML(html);
    const metadata = extractMetadata(parsed, url);
    console.log("   [OK] Title: " + (metadata.title || "(not found)"));
    if (metadata.date) console.log("   [OK] Date: " + metadata.date);

    // Determine output path EARLY so we can determine image path
    if (!outputPath) {
      await fs.mkdir(CONFIG.outputDir, { recursive: true });
      const filename = sanitizeFilename(metadata.title || "untitled") + ".md";
      outputPath = path.join(CONFIG.outputDir, filename);
    }

    // Set up image directory
    const outputDir = path.dirname(outputPath);
    await fs.mkdir(outputDir, { recursive: true });

    const baseName = path.basename(outputPath, path.extname(outputPath));
    const imageDirName = baseName + "_files"; // Using string concatenation
    const imageDir = path.join(outputDir, imageDirName);
    const relImagePrefix = imageDirName;

    // Process Images
    let contentToConvert = parsed.content;
    try {
        contentToConvert = await processImages(parsed.content, url, imageDir, relImagePrefix);
    } catch (e) {
        console.warn("   [WARN] Image processing failed, continuing: " + e.message);
    }

    const markdown = htmlToMarkdown(contentToConvert);
    console.log("   [OK] Content: " + markdown.length + " chars");

    // Generate output
    let output = "";
    output += "<!-- \n";
    output += "  Source: " + url + "\n";
    output += "  Crawled: " + new Date().toISOString() + "\n";
    if (metadata.date) output += "  Published: " + metadata.date + "\n";
    if (metadata.author) output += "  Author: " + metadata.author + "\n";
    output += "-->\n\n";

    if (metadata.title) {
      output += "# " + metadata.title + "\n\n";
    }

    if (metadata.description) {
      output += "> " + metadata.description + "\n\n";
    }

    output += markdown;

    await fs.writeFile(outputPath, output, "utf-8");
    console.log("   [OK] Saved: " + outputPath);

    return {
      success: true,
      url: url,
      outputPath: outputPath,
      metadata: metadata,
    };
  } catch (error) {
    console.error("   [ERROR] " + error.message);
    return { success: false, url: url, error: error.message };
  }
}

// ============ Main Function ============
async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log("");
    console.log("=".repeat(60));
    console.log("  Web to Markdown - Enhanced Web Page Crawler & Converter");
    console.log("=".repeat(60));
    console.log("");
    console.log("  Usage:");
    console.log("    node tools/web_to_md.cjs <url>");
    console.log("    node tools/web_to_md.cjs <url1> <url2> ...");
    console.log("    node tools/web_to_md.cjs -f urls.txt");
    console.log("    node tools/web_to_md.cjs <url> -o output.md");
    console.log("");
    console.log("  Options:");
    console.log("    -f, --file <file>    Read URLs from file (one per line)");
    console.log(
      "    -o, --output <file>  Specify output filename (single URL only)"
    );
    console.log(
      "    -d, --dir <dir>      Specify output directory (default: ./output)"
    );
    console.log("    -h, --help           Show help");
    console.log("");
    console.log("=".repeat(60));
    process.exit(0);
  }

  let urls = [];
  let outputFile = null;

  // Parse arguments
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === "-h" || arg === "--help") {
      args.length = 0;
      await main();
      return;
    }

    if (arg === "-f" || arg === "--file") {
      const filePath = args[++i];
      if (!filePath) {
        console.error("Error: -f requires a file path");
        process.exit(1);
      }
      const content = await fs.readFile(filePath, "utf-8");
      const lines = content
        .split("\n")
        .map(function (l) {
          return l.trim();
        })
        .filter(function (l) {
          return l && !l.startsWith("#");
        });
      urls = urls.concat(lines);
      continue;
    }

    if (arg === "-o" || arg === "--output") {
      outputFile = args[++i];
      continue;
    }

    if (arg === "-d" || arg === "--dir") {
      CONFIG.outputDir = args[++i];
      continue;
    }

    if (arg.startsWith("http://") || arg.startsWith("https://")) {
      urls.push(arg);
    }
  }

  if (urls.length === 0) {
    console.error("Error: No valid URLs provided");
    process.exit(1);
  }

  console.log("\n[Start] Processing " + urls.length + " URL(s)...");

  const results = [];
  for (let i = 0; i < urls.length; i++) {
    const result = await processUrl(
      urls[i],
      urls.length === 1 ? outputFile : null
    );
    results.push(result);
  }

  // Summary
  const success = results.filter(function (r) {
    return r.success;
  }).length;
  const failed = results.filter(function (r) {
    return !r.success;
  }).length;

  console.log("\n" + "=".repeat(50));
  console.log(
    "[Done] Success: " + success + "/" + urls.length + ", Failed: " + failed
  );

  if (failed > 0) {
    console.log("\n[Failed URLs]:");
    results
      .filter(function (r) {
        return !r.success;
      })
      .forEach(function (r) {
        console.log("   - " + r.url + ": " + r.error);
      });
  }
}

main().catch(console.error);
