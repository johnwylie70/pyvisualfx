#!/usr/bin/env node
/**
 * Python scenes in a real browser, run by `pyctures run`: the effects Python turned on are on in the page,
 * they are run once for each frame Python sends and on Python's clock, and the picture is the very one
 * the JavaScript library gives for the same drawing and the same effects.
 *
 *   PLAYWRIGHT=/path/to/node_modules/playwright node tests/test-browser.mjs
 *
 * Pyctures is the one installed, or its repository beside this one. PYTHON=python3.13 picks the Python.
 * Every Python twin of a demo in ../visualfx.js/demos is run too, and must show its picture with no error.
 */
import { spawn } from 'node:child_process'
import { existsSync, readdirSync } from 'node:fs'
import { createServer } from 'node:net'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const from = process.env.PLAYWRIGHT || 'playwright'
const playwright = await import(from.startsWith('/') ? pathToFileURL(join(from, 'index.mjs')).href : from)
const PYTHON = process.env.PYTHON || 'python3'
const freePort = () => new Promise((done) => { const s = createServer(); s.listen(0, () => { const { port } = s.address(); s.close(() => done(port)) }) })

async function run(file) {
  const port = await freePort()
  const env = { ...process.env, PYTHONPATH: [join(ROOT, 'src'), join(ROOT, '..', 'pyctures', 'src'), process.env.PYTHONPATH || ''].filter(Boolean).join(':') }
  const proc = spawn(PYTHON, ['-m', 'pyctures', 'run', file, '--no-browser', '--port', String(port)], { env, stdio: ['ignore', 'pipe', 'pipe'] })
  let said = ''
  proc.stdout.on('data', (d) => { said += d }); proc.stderr.on('data', (d) => { said += d })
  for (let i = 0; i < 100 && !/http:\/\/localhost/.test(said); i++) await new Promise((r) => setTimeout(r, 100))
  return { url: `http://localhost:${port}/`, said: () => said, stop: () => proc.kill() }
}
// What the page's effects are doing, read when a frame's picture is on the screen.
const READ = () => new Promise((done) => {
  const look = () => {
    const canvas = document.querySelector('canvas:not([data-effects-layer]):not([data-dials-layer])')
    const pipe = canvas && canvas[Symbol.for('effects.pipeline')]
    if (!pipe || !window.pyClock || window.pyClock[1] < 12) return setTimeout(look, 50)
    pipe.api.onFrame((fx) => {
      pipe.api.onFrame(null)
      const p = fx.pixels()
      done({ stats: fx.stats(), clock: window.pyClock, size: [canvas.width, canvas.height, canvas.clientWidth], data: Array.from(p.data), w: p.width, h: p.height,
        effects: pipe.effects.map((e) => ({ name: e.name, active: e.active, values: e.values })) })
    })
  }
  look()
})
// The same drawing and the same effects, by the JavaScript library alone, on a canvas of the same size.
const SAME = async ({ w, h, lib }) => {
  const { effects } = await import(lib)
  const canvas = Object.assign(document.createElement('canvas'), { width: w, height: h })
  canvas.style.cssText = `display:block;width:${w}px;height:${h}px`
  document.body.replaceChildren(canvas)
  const g = canvas.getContext('2d')
  g.fillStyle = 'black'; g.fillRect(0, 0, w, h)
  g.fillStyle = 'gold'; g.beginPath(); g.arc(120, 90, 40, 0, Math.PI * 2); g.fill()
  g.fillStyle = 'deepskyblue'; g.fillRect(40, 150, 90, 50)
  g.strokeStyle = 'tomato'; g.lineWidth = 6; g.beginPath(); g.moveTo(0, 0); g.lineTo(200, 120); g.stroke()
  const fx = effects(canvas, { manual: true })
  fx.mirror('four'); fx.blur(10); fx.hue(120)
  fx.frame(1 / 60)
  return Array.from(fx.pixels().data)
}

let failed = 0, ran = 0
const check = (what, ok, got) => { ran++; if (ok) return console.log(`  ok   ${what}`); failed++; console.log(`  FAIL ${what}\n       ${JSON.stringify(got)?.slice(0, 700)}`) }
const browser = await playwright.chromium.launch({ args: ['--mute-audio'] })

{
  const scene = await run(join(ROOT, 'tests', 'scene_parity.py'))
  const page = await browser.newPage({ viewport: { width: 640, height: 480 }, deviceScaleFactor: 1 })
  const errors = []
  page.on('pageerror', (e) => errors.push(e.message))
  await page.goto(scene.url)
  const got = await page.evaluate(READ)
  const names = got.effects.map((e) => `${e.name}:${e.active}`).join()
  check('the effects Python turned on are on in the page, in its order, and the one it turned off is off', names === 'mirror:true,blur:true,hue:true,glow:false', names)
  check('a setting changed from Python is the page\'s setting', got.effects[1].values.radius === 10 && got.effects[2].values.shift === 120 && got.effects[3].values.radius === 20, got.effects)
  check('the effects are run once for each frame Python sends, on Python\'s clock', Math.abs(got.stats.frames - got.clock[1]) <= 1 && Math.abs(got.stats.time - got.clock[0]) < 0.11 && got.clock[0] > 0, { stats: got.stats, clock: got.clock })
  await page.goto('about:blank')
  await page.goto(scene.url)
  await page.route('**/pyvisualfx-same.js', (route) => route.fulfill({ path: join(ROOT, 'src', 'pyvisualfx', 'web', 'visualfx.js'), contentType: 'text/javascript' }))
  const same = await page.evaluate(SAME, { w: got.w, h: got.h, lib: '/pyvisualfx-same.js' })
  let sum = 0, most = 0
  for (let i = 0; i < same.length; i++) { const d = Math.abs(same[i] - got.data[i]); sum += d; if (d > most) most = d }
  check('the picture is the one the JavaScript library gives for the same drawing and effects', same.length === got.data.length && sum / same.length < 0.2 && most <= 24, { mean: sum / same.length, most, size: got.size })
  check('the scene left no error on its page', errors.length === 0, errors)
  await page.close()
  scene.stop()
}

const demos = join(ROOT, '..', 'visualfx.js', 'demos')
for (const demo of existsSync(demos) ? readdirSync(demos).filter((d) => existsSync(join(demos, d, 'main.py'))) : []) {
  const scene = await run(join(demos, demo, 'main.py'))
  const page = await browser.newPage({ viewport: { width: 800, height: 500 }, deviceScaleFactor: 1 })
  const errors = []
  page.on('pageerror', (e) => errors.push(e.message))
  await page.goto(scene.url)
  const got = await page.evaluate(() => new Promise((done) => {
    const began = Date.now()
    const look = () => {
      const canvas = document.querySelector('canvas:not([data-effects-layer])'), pipe = canvas && canvas[Symbol.for('effects.pipeline')]
      if ((!pipe || pipe.frames < 40) && Date.now() - began < 8000) return setTimeout(look, 50)
      if (!pipe) return done({ none: true })
      pipe.api.onFrame((fx) => { pipe.api.onFrame(null); const p = fx.pixels(); let lit = 0; for (let i = 0; i < p.data.length; i += 4) if (p.data[i] + p.data[i + 1] + p.data[i + 2] > 60) lit++; done({ lit: lit / (p.width * p.height), frames: pipe.frames, effects: pipe.effects.length }) })
    }
    look()
  }))
  const trouble = /Traceback|Error/.test(scene.said()) ? scene.said().split('\n').slice(-6).join(' | ') : ''
  check(`the Python twin of the ${demo} demo runs and shows its picture`, !got.none && got.lit > 0.01 && got.effects >= 2 && !errors.length && !trouble, { got, errors, trouble })
  await page.close()
  scene.stop()
}
await browser.close()
console.log(failed ? `\n${failed} of ${ran} failed` : `\nall ${ran} passed`)
process.exit(failed ? 1 : 0)
