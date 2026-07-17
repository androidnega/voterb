<template>
  <div class="student-results">
    <header class="page-intro">
      <p class="page-greeting">Official outcomes</p>
      <h1 class="page-title">Published results</h1>
      <p class="page-sub">Certified election results you can review anytime.</p>
    </header>

    <FriendlyLoadState
      v-if="loading"
      title="Loading results"
      message="Fetching published elections…"
    />

    <FriendlyLoadState
      v-else-if="error"
      tone="error"
      title="Couldn’t load results"
      :message="error"
      action-label="Try again"
      @action="fetchPublishedResults"
    />

    <FriendlyLoadState
      v-else-if="!results.length"
      tone="empty"
      title="No results yet"
      message="When an election is certified and published, it will show up here."
      icon="far fa-chart-bar"
    />

    <div v-else class="results-list">
      <article
        v-for="result in results"
        :key="result.uuid"
        class="result-card"
        @click="viewResult(result.election?.uuid || result.uuid)"
      >
        <div class="result-card__main">
          <div class="result-card__head">
            <h2>{{ result.election?.title || 'Election' }}</h2>
            <span class="result-badge">Published</span>
          </div>
          <p v-if="result.election?.description" class="result-desc">
            {{ result.election.description }}
          </p>
          <div class="result-meta">
            <span>Turnout {{ result.turnout_percentage || 0 }}%</span>
            <span v-if="result.published_at">{{ formatDate(result.published_at) }}</span>
            <span v-if="certifiedByLabel(result)">Certified by {{ certifiedByLabel(result) }}</span>
          </div>
        </div>
        <div class="result-card__footer">
          <button type="button" class="result-action">
            View results
            <i class="fas fa-arrow-right" aria-hidden="true"></i>
          </button>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { resultsApi } from '@/api/results'
import FriendlyLoadState from '@/components/student/FriendlyLoadState.vue'

const router = useRouter()
const results = ref([])
const loading = ref(true)
const error = ref(null)

function normalizeList(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.results)) return data.results
  return []
}

const certifiedByLabel = (result) =>
  result.certified_by_email
  || result.certified_by?.email
  || result.certified_by_name
  || result.certified_by?.display_name
  || ''

const fetchPublishedResults = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await resultsApi.getPublished()
    results.value = normalizeList(response.data)
  } catch (err) {
    console.error('Failed to fetch published results:', err)
    error.value = 'Could not load results. Please try again later.'
    results.value = []
  } finally {
    loading.value = false
  }
}

const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString('en-GB', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const viewResult = (uuid) => {
  if (!uuid) return
  router.push(`/student/results/${uuid}`)
}

onMounted(fetchPublishedResults)
</script>

<style scoped>
.student-results {
  display: grid;
  gap: 1.5rem;
}

.page-intro {
  display: grid;
  gap: 0.35rem;
}

.page-greeting {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 500;
  color: #a8a29e;
}

.page-title {
  margin: 0;
  font-size: clamp(1.35rem, 5vw, 1.85rem);
  font-weight: 700;
  letter-spacing: -0.035em;
  color: #1c1917;
  line-height: 1.1;
}

.page-sub {
  margin: 0.15rem 0 0;
  font-size: 0.78rem;
  color: #78716c;
  line-height: 1.45;
}

.results-list {
  display: grid;
  gap: 0.65rem;
}

.result-card {
  background: #fff;
  border: 1px solid #ebe8e2;
  border-radius: 0.85rem;
  overflow: hidden;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.result-card:hover {
  border-color: #d1fae5;
  box-shadow: 0 8px 24px rgba(15, 118, 110, 0.06);
}

.result-card__main {
  padding: 1rem 1rem 0.75rem;
  display: grid;
  gap: 0.45rem;
}

.result-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.65rem;
}

.result-card__head h2 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #1c1917;
  line-height: 1.3;
}

.result-badge {
  flex-shrink: 0;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #0f766e;
  background: #ecfdf5;
  border: 1px solid #d1fae5;
  border-radius: 999px;
  padding: 0.28rem 0.55rem;
}

.result-desc {
  margin: 0;
  font-size: 0.74rem;
  line-height: 1.5;
  color: #78716c;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.85rem;
  font-size: 0.68rem;
  font-weight: 500;
  color: #a8a29e;
}

.result-card__footer {
  padding: 0.55rem 0.85rem 0.85rem;
  display: flex;
  justify-content: flex-end;
}

.result-action {
  border: none;
  background: transparent;
  color: #0f766e;
  font-size: 0.74rem;
  font-weight: 650;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0;
}

.result-action i {
  font-size: 0.58rem;
}

@media (min-width: 768px) {
  .student-results {
    max-width: 34rem;
    margin: 0 auto;
    width: 100%;
    gap: 2rem;
  }

  .result-card {
    border-radius: 1rem;
  }

  .result-card__main {
    padding: 1.2rem 1.25rem 0.85rem;
  }

  .result-card__footer {
    padding: 0 1.25rem 1.15rem;
  }

  .result-card__head h2 {
    font-size: 1.05rem;
  }
}
</style>
