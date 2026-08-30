import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const assetRoot = path.resolve(scriptDir, '..', '제출', 'assets', 'pipeline_icons');
const sheetRoot = path.join(assetRoot, 'sheets');

const sets = [
  {
    sheet: 'icon_sheet_exact_01.png',
    names: [
      '01_사업장_재무정보.png',
      '02_서울_상권업종데이터.png',
      '03_공식_정책공고.png',
      '04_상권환경_분석.png',
      '05_정책탐색_자격확인.png',
      '06_금융계산_엔진.png',
    ],
  },
  {
    sheet: 'icon_sheet_exact_02.png',
    names: [
      '07_13주_예상현금.png',
      '08_6개월_예상현금부채.png',
      '09_무대응대비_변화.png',
      '10_진단.png',
      '11_비교.png',
      '12_신청준비.png',
    ],
  },
  {
    sheet: 'icon_sheet_exact_03.png',
    names: [
      '13_사용자동의.png',
      '14_Luna_보조.png',
      '15_What-if_해석.png',
      '16_공고핵심정보_정리.png',
      '17_정책근거_설명.png',
      '18_서버검증.png',
    ],
  },
];

function paeth(a, b, c) {
  const p = a + b - c;
  const pa = Math.abs(p - a);
  const pb = Math.abs(p - b);
  const pc = Math.abs(p - c);
  if (pa <= pb && pa <= pc) return a;
  return pb <= pc ? b : c;
}

function decodePng(filePath) {
  const input = fs.readFileSync(filePath);
  const signature = input.subarray(0, 8);
  if (!signature.equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))) {
    throw new Error(`Not a PNG: ${filePath}`);
  }

  let offset = 8;
  let ihdr;
  let palette;
  let transparency;
  const idat = [];
  while (offset < input.length) {
    const length = input.readUInt32BE(offset);
    const type = input.toString('ascii', offset + 4, offset + 8);
    const data = input.subarray(offset + 8, offset + 8 + length);
    if (type === 'IHDR') ihdr = data;
    if (type === 'PLTE') palette = data;
    if (type === 'tRNS') transparency = data;
    if (type === 'IDAT') idat.push(data);
    offset += 12 + length;
    if (type === 'IEND') break;
  }
  if (!ihdr || idat.length === 0) throw new Error(`Incomplete PNG: ${filePath}`);

  const width = ihdr.readUInt32BE(0);
  const height = ihdr.readUInt32BE(4);
  const bitDepth = ihdr[8];
  const colorType = ihdr[9];
  const interlace = ihdr[12];
  if (bitDepth !== 8 || interlace !== 0) {
    throw new Error(`Unsupported PNG format: bitDepth=${bitDepth}, interlace=${interlace}`);
  }

  const sourceChannels = { 0: 1, 2: 3, 3: 1, 4: 2, 6: 4 }[colorType];
  if (!sourceChannels) throw new Error(`Unsupported PNG color type: ${colorType}`);
  const stride = width * sourceChannels;
  const inflated = zlib.inflateSync(Buffer.concat(idat));
  const rows = Buffer.alloc(stride * height);
  let sourceOffset = 0;

  for (let y = 0; y < height; y += 1) {
    const filter = inflated[sourceOffset++];
    const rowOffset = y * stride;
    const previousOffset = (y - 1) * stride;
    for (let x = 0; x < stride; x += 1) {
      const raw = inflated[sourceOffset++];
      const left = x >= sourceChannels ? rows[rowOffset + x - sourceChannels] : 0;
      const up = y > 0 ? rows[previousOffset + x] : 0;
      const upLeft = y > 0 && x >= sourceChannels ? rows[previousOffset + x - sourceChannels] : 0;
      let value;
      if (filter === 0) value = raw;
      else if (filter === 1) value = raw + left;
      else if (filter === 2) value = raw + up;
      else if (filter === 3) value = raw + Math.floor((left + up) / 2);
      else if (filter === 4) value = raw + paeth(left, up, upLeft);
      else throw new Error(`Unsupported PNG filter: ${filter}`);
      rows[rowOffset + x] = value & 0xff;
    }
  }

  const rgba = Buffer.alloc(width * height * 4);
  for (let i = 0; i < width * height; i += 1) {
    const sourceIndex = i * sourceChannels;
    const targetIndex = i * 4;
    if (colorType === 6) {
      rows.copy(rgba, targetIndex, sourceIndex, sourceIndex + 4);
    } else if (colorType === 2) {
      rgba[targetIndex] = rows[sourceIndex];
      rgba[targetIndex + 1] = rows[sourceIndex + 1];
      rgba[targetIndex + 2] = rows[sourceIndex + 2];
      rgba[targetIndex + 3] = 255;
    } else if (colorType === 0) {
      rgba[targetIndex] = rows[sourceIndex];
      rgba[targetIndex + 1] = rows[sourceIndex];
      rgba[targetIndex + 2] = rows[sourceIndex];
      rgba[targetIndex + 3] = 255;
    } else if (colorType === 4) {
      rgba[targetIndex] = rows[sourceIndex];
      rgba[targetIndex + 1] = rows[sourceIndex];
      rgba[targetIndex + 2] = rows[sourceIndex];
      rgba[targetIndex + 3] = rows[sourceIndex + 1];
    } else {
      const paletteIndex = rows[sourceIndex];
      rgba[targetIndex] = palette[paletteIndex * 3];
      rgba[targetIndex + 1] = palette[paletteIndex * 3 + 1];
      rgba[targetIndex + 2] = palette[paletteIndex * 3 + 2];
      rgba[targetIndex + 3] = transparency?.[paletteIndex] ?? 255;
    }
  }
  return { width, height, rgba };
}

const crcTable = new Uint32Array(256).map((_, n) => {
  let c = n;
  for (let k = 0; k < 8; k += 1) c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
  return c >>> 0;
});

function crc32(buffer) {
  let c = 0xffffffff;
  for (const byte of buffer) c = crcTable[(c ^ byte) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function pngChunk(type, data) {
  const typeBuffer = Buffer.from(type, 'ascii');
  const chunk = Buffer.alloc(data.length + 12);
  chunk.writeUInt32BE(data.length, 0);
  typeBuffer.copy(chunk, 4);
  data.copy(chunk, 8);
  chunk.writeUInt32BE(crc32(Buffer.concat([typeBuffer, data])), data.length + 8);
  return chunk;
}

function encodePng(width, height, rgba) {
  const signature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8;
  ihdr[9] = 6;
  const raw = Buffer.alloc((width * 4 + 1) * height);
  for (let y = 0; y < height; y += 1) {
    const targetOffset = y * (width * 4 + 1);
    raw[targetOffset] = 0;
    rgba.copy(raw, targetOffset + 1, y * width * 4, (y + 1) * width * 4);
  }
  return Buffer.concat([
    signature,
    pngChunk('IHDR', ihdr),
    pngChunk('IDAT', zlib.deflateSync(raw, { level: 9 })),
    pngChunk('IEND', Buffer.alloc(0)),
  ]);
}

function alphaStats(rgba) {
  let min = 255;
  let max = 0;
  let transparentPixels = 0;
  for (let i = 3; i < rgba.length; i += 4) {
    const alpha = rgba[i];
    if (alpha < min) min = alpha;
    if (alpha > max) max = alpha;
    if (alpha < 255) transparentPixels += 1;
  }
  return { min, max, transparentPixels };
}

function removeConnectedLightBackground(rgba, width, height) {
  const pixelCount = width * height;
  const visited = new Uint8Array(pixelCount);
  const queue = new Int32Array(pixelCount);
  let head = 0;
  let tail = 0;

  const isBackground = (pixelIndex) => {
    const offset = pixelIndex * 4;
    const red = rgba[offset];
    const green = rgba[offset + 1];
    const blue = rgba[offset + 2];
    const minimum = Math.min(red, green, blue);
    const maximum = Math.max(red, green, blue);
    return minimum >= 220 && maximum - minimum <= 10;
  };

  const enqueue = (pixelIndex) => {
    if (visited[pixelIndex] || !isBackground(pixelIndex)) return;
    visited[pixelIndex] = 1;
    queue[tail++] = pixelIndex;
  };

  for (let x = 0; x < width; x += 1) {
    enqueue(x);
    enqueue((height - 1) * width + x);
  }
  for (let y = 1; y < height - 1; y += 1) {
    enqueue(y * width);
    enqueue(y * width + width - 1);
  }

  while (head < tail) {
    const pixelIndex = queue[head++];
    const x = pixelIndex % width;
    const y = Math.floor(pixelIndex / width);
    if (x > 0) enqueue(pixelIndex - 1);
    if (x + 1 < width) enqueue(pixelIndex + 1);
    if (y > 0) enqueue(pixelIndex - width);
    if (y + 1 < height) enqueue(pixelIndex + width);
  }

  for (let pixelIndex = 0; pixelIndex < pixelCount; pixelIndex += 1) {
    if (visited[pixelIndex]) rgba[pixelIndex * 4 + 3] = 0;
  }
  return tail;
}

fs.mkdirSync(assetRoot, { recursive: true });
let total = 0;
for (const set of sets) {
  const sourcePath = path.join(sheetRoot, set.sheet);
  const source = decodePng(sourcePath);
  if (source.width % 3 !== 0 || source.height % 2 !== 0) {
    throw new Error(`Sheet is not divisible into 3x2: ${set.sheet}`);
  }
  const tileWidth = source.width / 3;
  const tileHeight = source.height / 2;
  console.log(`SHEET ${set.sheet}: ${source.width}x${source.height}; tile ${tileWidth}x${tileHeight}`);

  for (let index = 0; index < 6; index += 1) {
    const column = index % 3;
    const row = Math.floor(index / 3);
    const tile = Buffer.alloc(tileWidth * tileHeight * 4);
    for (let y = 0; y < tileHeight; y += 1) {
      const sourceStart = (((row * tileHeight + y) * source.width) + column * tileWidth) * 4;
      const targetStart = y * tileWidth * 4;
      source.rgba.copy(tile, targetStart, sourceStart, sourceStart + tileWidth * 4);
    }
    const removedBackgroundPixels = removeConnectedLightBackground(tile, tileWidth, tileHeight);
    const outputPath = path.join(assetRoot, set.names[index]);
    fs.writeFileSync(outputPath, encodePng(tileWidth, tileHeight, tile));
    const stats = alphaStats(tile);
    console.log(`ICON ${set.names[index]}: ${tileWidth}x${tileHeight}; alpha ${stats.min}-${stats.max}; transparent ${stats.transparentPixels}; removed ${removedBackgroundPixels}`);
    total += 1;
  }
}
console.log(`TOTAL ${total}`);
