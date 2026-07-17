<template>
  <div class="admin-page ceremony">
    <header class="ceremony-hero">
      <button type="button" class="ceremony-back" @click="goBack">
        <i class="fas fa-arrow-left" aria-hidden="true"></i>
        Results
      </button>
      <p class="ceremony-eyebrow">Certification</p>
      <h1 class="ceremony-title">Certify results</h1>
      <p class="ceremony-sub">
        {{ electionTitle || 'Election results' }} — photo, location, and signature required.
      </p>
    </header>

    <nav class="ceremony-rail" aria-label="Certification steps">
      <div
        v-for="s in steps"
        :key="s.id"
        class="ceremony-rail__item"
        :class="{
          'is-active': step === s.id,
          'is-done': step > s.id,
        }"
      >
        <span class="ceremony-rail__dot" aria-hidden="true">
          <i v-if="step > s.id" class="fas fa-check"></i>
          <span v-else>{{ s.id }}</span>
        </span>
        <span class="ceremony-rail__label">{{ s.label }}</span>
      </div>
    </nav>

    <!-- Step 1: Photo -->
    <section v-if="step === 1" class="ceremony-panel">
      <div class="ceremony-panel__intro">
        <h2>Certifier photo</h2>
        <p>Capture a clear headshot for the official record.</p>
      </div>

      <div class="photo-stage">
        <video v-show="!photoDataUrl" ref="videoEl" class="photo-stage__media" autoplay playsinline muted />
        <img v-if="photoDataUrl" :src="photoDataUrl" alt="Captured photo" class="photo-stage__media" />
        <canvas ref="photoCanvasEl" hidden />
        <div v-if="!photoDataUrl && !stream && !startingCamera" class="photo-stage__empty">
          <i class="fas fa-camera" aria-hidden="true"></i>
          <span>Camera off</span>
        </div>
      </div>

      <p v-if="cameraError" class="ceremony-error">{{ cameraError }}</p>

      <div class="ceremony-actions">
        <button v-if="!photoDataUrl" type="button" class="btn btn-ghost" :disabled="startingCamera" @click="startCamera">
          <i v-if="startingCamera" class="fas fa-spinner fa-spin"></i>
          <i v-else class="fas fa-video"></i>
          {{ stream ? 'Restart camera' : 'Start camera' }}
        </button>
        <button v-if="stream && !photoDataUrl" type="button" class="btn btn-primary" @click="capturePhoto">
          <i class="fas fa-camera"></i>
          Capture
        </button>
        <button v-if="photoDataUrl" type="button" class="btn btn-ghost" @click="retakePhoto">
          Retake
        </button>
        <button type="button" class="btn btn-primary" :disabled="!photoDataUrl" @click="step = 2">
          Continue
        </button>
      </div>
    </section>

    <!-- Step 2: Location -->
    <section v-else-if="step === 2" class="ceremony-panel">
      <div class="ceremony-panel__intro">
        <h2>Location</h2>
        <p>Use GPS, or enter coordinates if GPS is unavailable.</p>
      </div>

      <div v-if="location" class="location-card">
        <div class="location-card__row">
          <span>Latitude</span>
          <strong>{{ location.lat }}</strong>
        </div>
        <div class="location-card__row">
          <span>Longitude</span>
          <strong>{{ location.lng }}</strong>
        </div>
        <div v-if="location.accuracy != null" class="location-card__row">
          <span>Accuracy</span>
          <strong>±{{ Math.round(location.accuracy) }}m</strong>
        </div>
        <div class="location-card__row">
          <span>Source</span>
          <strong class="location-card__source">{{ location.source }}</strong>
        </div>
      </div>
      <div v-else class="location-empty">
        No location captured yet.
      </div>

      <p v-if="locationError" class="ceremony-error">{{ locationError }}</p>

      <div class="manual-location">
        <label>
          Manual latitude
          <InputText v-model="manualLat" class="w-full" placeholder="e.g. 6.6885" />
        </label>
        <label>
          Manual longitude
          <InputText v-model="manualLng" class="w-full" placeholder="e.g. -1.6244" />
        </label>
      </div>

      <div class="ceremony-actions">
        <button type="button" class="btn btn-ghost" @click="step = 1">Back</button>
        <button type="button" class="btn btn-ghost" :disabled="locating" @click="captureGps">
          <i v-if="locating" class="fas fa-spinner fa-spin"></i>
          <i v-else class="fas fa-map-marker-alt"></i>
          Use GPS
        </button>
        <button type="button" class="btn btn-ghost" @click="applyManualLocation">Use manual</button>
        <button type="button" class="btn btn-primary" :disabled="!location" @click="goToSignature">
          Continue
        </button>
      </div>
    </section>

    <!-- Step 3: Signature -->
    <section v-else-if="step === 3" class="ceremony-panel">
      <div class="ceremony-panel__intro">
        <h2>Signature</h2>
        <p>Sign in the box below with your mouse or finger.</p>
      </div>

      <div class="sig-wrap">
        <canvas
          ref="sigCanvasEl"
          class="sig-canvas"
          width="640"
          height="220"
          @pointerdown="onSigPointerDown"
          @pointermove="onSigPointerMove"
          @pointerup="onSigPointerUp"
          @pointerleave="onSigPointerUp"
        />
      </div>

      <div class="ceremony-actions">
        <button type="button" class="btn btn-ghost" @click="step = 2">Back</button>
        <button type="button" class="btn btn-ghost" @click="clearSignature">Clear</button>
        <button type="button" class="btn btn-primary" :disabled="!hasSignature" @click="goToConfirm">
          Continue
        </button>
      </div>
    </section>

    <!-- Step 4: Confirm -->
    <section v-else class="ceremony-panel">
      <div class="ceremony-panel__intro">
        <h2>Review &amp; certify</h2>
        <p>Confirm the evidence. IP and device fingerprint are recorded automatically.</p>
      </div>

      <div class="confirm-grid">
        <div class="confirm-card confirm-card--photo">
          <h3>Photo</h3>
          <img v-if="photoDataUrl" :src="photoDataUrl" alt="Certifier photo" class="confirm-photo" />
        </div>
        <div class="confirm-card">
          <h3>Location</h3>
          <p v-if="location" class="confirm-value">{{ location.lat }}, {{ location.lng }}</p>
          <p class="confirm-muted">{{ location?.source }}</p>
        </div>
        <div class="confirm-card">
          <h3>Signature</h3>
          <img v-if="signatureDataUrl" :src="signatureDataUrl" alt="Signature" class="confirm-sig" />
        </div>
        <div class="confirm-card">
          <h3>Device</h3>
          <p class="confirm-value"><span>IP</span> {{ clientIp || '…' }}</p>
          <p class="confirm-muted mono fingerprint">{{ fingerprint }}</p>
        </div>
      </div>

      <p v-if="submitError" class="ceremony-error">{{ submitError }}</p>

      <div class="ceremony-actions">
        <button type="button" class="btn btn-ghost" :disabled="submitting" @click="step = 3">Back</button>
        <button type="button" class="btn btn-primary" :disabled="submitting || !canSubmit" @click="submitCertification">
          <i v-if="submitting" class="fas fa-spinner fa-spin"></i>
          <i v-else class="fas fa-stamp"></i>
          {{ submitting ? 'Certifying…' : 'Certify results' }}
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import InputText from 'primevue/inputtext'
import { resultsApi } from '@/api/results'
import { collectVoteAuditContext } from '@/utils/deviceAudit'
import { usePageHeading } from '@/composables/usePageHeading'

const route = useRoute()
const router = useRouter()
const { setPageHeading } = usePageHeading()
setPageHeading({
  title: 'Certification ceremony',
  subtitle: 'Photo, location, and signature required to certify results.',
})

const steps = [
  { id: 1, label: 'Photo' },
  { id: 2, label: 'Location' },
  { id: 3, label: 'Signature' },
  { id: 4, label: 'Confirm' },
]

const step = ref(1)
const electionTitle = ref('')
const photoDataUrl = ref('')
const signatureDataUrl = ref('')
const location = ref(null)
const manualLat = ref('')
const manualLng = ref('')
const fingerprint = ref('')
const clientIp = ref('')
const cameraError = ref('')
const locationError = ref('')
const submitError = ref('')
const startingCamera = ref(false)
const locating = ref(false)
const submitting = ref(false)
const hasSignature = ref(false)

const videoEl = ref(null)
const photoCanvasEl = ref(null)
const sigCanvasEl = ref(null)
const stream = ref(null)
let drawing = false
let lastPoint = null

const canSubmit = computed(() =>
  Boolean(photoDataUrl.value && location.value && signatureDataUrl.value && fingerprint.value)
)

const goBack = () => router.push(`/results/${route.params.uuid}`)

const stopCamera = () => {
  if (stream.value) {
    stream.value.getTracks().forEach((t) => t.stop())
    stream.value = null
  }
}

const startCamera = async () => {
  cameraError.value = ''
  startingCamera.value = true
  stopCamera()
  try {
    const media = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false,
    })
    stream.value = media
    await nextTick()
    if (videoEl.value) {
      videoEl.value.srcObject = media
      await videoEl.value.play()
    }
  } catch (err) {
    cameraError.value = err?.message || 'Unable to access camera. Check browser permissions.'
  } finally {
    startingCamera.value = false
  }
}

const capturePhoto = () => {
  const video = videoEl.value
  const canvas = photoCanvasEl.value
  if (!video || !canvas) return
  const w = video.videoWidth || 640
  const h = video.videoHeight || 480
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d')
  ctx.drawImage(video, 0, 0, w, h)
  photoDataUrl.value = canvas.toDataURL('image/jpeg', 0.85)
  stopCamera()
}

const retakePhoto = async () => {
  photoDataUrl.value = ''
  await startCamera()
}

const captureGps = () => {
  locationError.value = ''
  locating.value = true
  if (!navigator.geolocation) {
    locationError.value = 'Geolocation is not available. Enter coordinates manually.'
    locating.value = false
    return
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      location.value = {
        lat: Number(pos.coords.latitude.toFixed(6)),
        lng: Number(pos.coords.longitude.toFixed(6)),
        accuracy: pos.coords.accuracy,
        source: 'gps',
      }
      locating.value = false
    },
    (err) => {
      locationError.value = err?.message || 'GPS failed. Enter coordinates manually.'
      locating.value = false
    },
    { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 }
  )
}

const applyManualLocation = () => {
  const lat = Number(manualLat.value)
  const lng = Number(manualLng.value)
  if (Number.isNaN(lat) || Number.isNaN(lng)) {
    locationError.value = 'Enter valid numeric latitude and longitude.'
    return
  }
  if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
    locationError.value = 'Latitude must be -90…90 and longitude -180…180.'
    return
  }
  locationError.value = ''
  location.value = { lat, lng, accuracy: null, source: 'manual' }
}

const initSigCanvas = () => {
  const canvas = sigCanvasEl.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#fff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  ctx.strokeStyle = '#1c1917'
  ctx.lineWidth = 2.5
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  hasSignature.value = false
  signatureDataUrl.value = ''
}

const pointerPos = (e) => {
  const canvas = sigCanvasEl.value
  const rect = canvas.getBoundingClientRect()
  const scaleX = canvas.width / rect.width
  const scaleY = canvas.height / rect.height
  return {
    x: (e.clientX - rect.left) * scaleX,
    y: (e.clientY - rect.top) * scaleY,
  }
}

const onSigPointerDown = (e) => {
  drawing = true
  lastPoint = pointerPos(e)
  sigCanvasEl.value?.setPointerCapture?.(e.pointerId)
}

const onSigPointerMove = (e) => {
  if (!drawing || !sigCanvasEl.value) return
  const ctx = sigCanvasEl.value.getContext('2d')
  const point = pointerPos(e)
  ctx.beginPath()
  ctx.moveTo(lastPoint.x, lastPoint.y)
  ctx.lineTo(point.x, point.y)
  ctx.stroke()
  lastPoint = point
  hasSignature.value = true
}

const onSigPointerUp = () => {
  drawing = false
  lastPoint = null
}

const clearSignature = () => initSigCanvas()

const goToSignature = async () => {
  step.value = 3
  await nextTick()
  initSigCanvas()
}

const goToConfirm = async () => {
  if (!hasSignature.value || !sigCanvasEl.value) return
  signatureDataUrl.value = sigCanvasEl.value.toDataURL('image/png')
  step.value = 4
  try {
    const { data } = await resultsApi.certifyMeta(route.params.uuid, fingerprint.value)
    clientIp.value = data.ip_address || 'Unavailable'
  } catch {
    clientIp.value = 'Captured on submit'
  }
}

const submitCertification = async () => {
  submitError.value = ''
  submitting.value = true
  try {
    await resultsApi.certify(route.params.uuid, {
      certification_evidence: {
        photo: photoDataUrl.value,
        location: {
          lat: location.value.lat,
          lng: location.value.lng,
          accuracy: location.value.accuracy,
          source: location.value.source,
        },
        signature: signatureDataUrl.value,
        device_fingerprint: fingerprint.value,
      },
    }, fingerprint.value)
    router.push(`/results/${route.params.uuid}`)
  } catch (err) {
    submitError.value =
      err?.response?.data?.error
      || err?.response?.data?.detail
      || 'Certification failed. Please try again.'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    const { data } = await resultsApi.preview(route.params.uuid)
    electionTitle.value = data?.election?.title || ''
    if (!['generated', 'pending_certification'].includes(data?.status)) {
      router.replace(`/results/${route.params.uuid}`)
      return
    }
  } catch {
    router.replace('/results')
    return
  }

  const ctx = await collectVoteAuditContext({ includeLocation: false })
  fingerprint.value = ctx.fingerprint || ''
  await startCamera()
})

onBeforeUnmount(() => {
  stopCamera()
})
</script>

<style scoped>
.ceremony {
  max-width: 42rem;
  margin: 0 auto;
}

.ceremony-hero {
  display: grid;
  gap: 0.35rem;
  margin-bottom: 1.35rem;
}

.ceremony-back {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  width: fit-content;
  border: none;
  background: transparent;
  color: #78716c;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  margin-bottom: 0.45rem;
}

.ceremony-eyebrow {
  margin: 0;
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #a8a29e;
}

.ceremony-title {
  margin: 0;
  font-size: clamp(1.35rem, 3vw, 1.7rem);
  font-weight: 750;
  letter-spacing: -0.035em;
  color: #1c1917;
  line-height: 1.15;
}

.ceremony-sub {
  margin: 0;
  color: #78716c;
  font-size: 0.88rem;
  line-height: 1.45;
  max-width: 34rem;
}

.ceremony-rail {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.35rem;
  margin: 0 0 1.25rem;
  padding: 0.55rem;
  background: #fff;
  border: 1px solid #ebe8e2;
  border-radius: 999px;
}

.ceremony-rail__item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  padding: 0.45rem 0.55rem;
  border-radius: 999px;
  color: #a8a29e;
  font-size: 0.74rem;
  font-weight: 650;
  transition: background 0.16s ease, color 0.16s ease;
}

.ceremony-rail__dot {
  width: 1.35rem;
  height: 1.35rem;
  border-radius: 999px;
  display: inline-grid;
  place-items: center;
  font-size: 0.64rem;
  font-weight: 750;
  background: #f5f5f4;
  flex-shrink: 0;
}

.ceremony-rail__item.is-active {
  background: #1c1917;
  color: #fff;
}

.ceremony-rail__item.is-active .ceremony-rail__dot {
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
}

.ceremony-rail__item.is-done {
  color: #0f766e;
}

.ceremony-rail__item.is-done .ceremony-rail__dot {
  background: #ecfdf5;
  color: #0f766e;
}

.ceremony-panel {
  background: #fff;
  border: 1px solid #ebe8e2;
  border-radius: 1.15rem;
  padding: 1.25rem 1.3rem 1.3rem;
  animation: pane-in 0.22s ease;
}

.ceremony-panel__intro {
  margin-bottom: 1.05rem;
}

.ceremony-panel__intro h2 {
  margin: 0 0 0.25rem;
  font-size: 1.05rem;
  font-weight: 750;
  letter-spacing: -0.02em;
  color: #1c1917;
}

.ceremony-panel__intro p {
  margin: 0;
  color: #78716c;
  font-size: 0.84rem;
  line-height: 1.45;
}

.photo-stage {
  position: relative;
  max-width: 22rem;
  aspect-ratio: 4 / 3;
  background: #1c1917;
  border-radius: 1rem;
  overflow: hidden;
  margin-bottom: 1rem;
}

.photo-stage__media {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.photo-stage__empty {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  gap: 0.4rem;
  color: #a8a29e;
  font-size: 0.78rem;
  font-weight: 600;
  text-align: center;
}

.photo-stage__empty i {
  font-size: 1.25rem;
  opacity: 0.7;
}

.ceremony-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1rem;
}

.ceremony-error {
  color: #b91c1c;
  font-size: 0.82rem;
  margin: 0.55rem 0 0;
}

.location-card {
  display: grid;
  gap: 0.45rem;
  margin-bottom: 1rem;
  max-width: 22rem;
  padding: 0.85rem 1rem;
  border-radius: 0.9rem;
  background: #fafaf8;
  border: 1px solid #ebe8e2;
}

.location-card__row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
  font-size: 0.82rem;
}

.location-card__row span {
  color: #a8a29e;
}

.location-card__row strong {
  color: #1c1917;
  font-weight: 650;
  font-variant-numeric: tabular-nums;
}

.location-card__source {
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: 0.72rem;
}

.location-empty {
  max-width: 22rem;
  margin-bottom: 1rem;
  padding: 0.85rem 1rem;
  border-radius: 0.9rem;
  border: 1px dashed #e7e5e4;
  color: #a8a29e;
  font-size: 0.82rem;
}

.manual-location {
  display: grid;
  gap: 0.65rem;
  margin-bottom: 0.25rem;
  max-width: 22rem;
}

.manual-location label {
  display: grid;
  gap: 0.3rem;
  font-size: 0.74rem;
  font-weight: 650;
  color: #57534e;
}

.sig-wrap {
  border: 1px solid #ebe8e2;
  border-radius: 0.95rem;
  background: #fafaf8;
  padding: 0.55rem;
  max-width: 40rem;
}

.sig-canvas {
  width: 100%;
  height: auto;
  border-radius: 0.7rem;
  touch-action: none;
  cursor: crosshair;
  background: #fff;
  display: block;
}

.confirm-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.75rem;
}

@media (min-width: 720px) {
  .confirm-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.confirm-card {
  border: 1px solid #ebe8e2;
  border-radius: 0.95rem;
  padding: 0.9rem;
  background: #fafaf8;
}

.confirm-card h3 {
  margin: 0 0 0.55rem;
  font-size: 0.68rem;
  font-weight: 700;
  color: #a8a29e;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.confirm-value {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 650;
  color: #1c1917;
  line-height: 1.4;
}

.confirm-value span {
  display: inline-block;
  margin-right: 0.35rem;
  color: #a8a29e;
  font-weight: 600;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.confirm-muted {
  margin: 0.3rem 0 0;
  color: #a8a29e;
  font-size: 0.78rem;
}

.confirm-photo,
.confirm-sig {
  max-width: 100%;
  border-radius: 0.7rem;
  background: #fff;
  border: 1px solid #ebe8e2;
}

.fingerprint {
  word-break: break-all;
  font-size: 0.7rem;
  line-height: 1.4;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

@keyframes pane-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@media (max-width: 640px) {
  .ceremony-rail {
    border-radius: 1rem;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .ceremony-rail__label {
    font-size: 0.7rem;
  }

  .ceremony-panel {
    padding: 1.05rem 1rem 1.1rem;
  }
}
</style>
