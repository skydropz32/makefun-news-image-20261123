// Entry for make.fun news-image-20261123 (Node 22, standard library only).
// The front page is entry.png, drawn at build time by draw.py (Python
// standard library only, deterministic, no network). This program copies it
// to the output directory the grader provides.
//
// Run locally with:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
mkdirSync(outDir, { recursive: true });
copyFileSync(new URL('./entry.png', import.meta.url), join(outDir, 'entry.png'));
