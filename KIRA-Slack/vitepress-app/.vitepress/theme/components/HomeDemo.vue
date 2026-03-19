<script setup>
import { computed } from 'vue'
import { useData } from 'vitepress'

const { lang } = useData()

const title = computed(() => (lang.value === 'ko-KR' ? '데모' : 'Demo'))

const videos = [
  [
    {
      title: 'Search + PPTX',
      src: 'https://github.com/user-attachments/assets/284f9d0d-056c-42e9-8f1f-19873431ddba'
    },
    {
      title: 'GitRepo + PDF',
      src: 'https://github.com/user-attachments/assets/721bc704-8b1a-4673-829a-52309ae69601'
    },
    {
      title: 'Web + Wiki',
      src: 'https://github.com/user-attachments/assets/7329039a-fdad-4f4b-8f03-65402e4d6f6c'
    }
  ],
  [
    {
      title: 'Proactive + Thread',
      src: 'https://github.com/user-attachments/assets/9ee1a520-507c-408a-a1d2-4a7a393385eb'
    },
    {
      title: 'Email + Schedule',
      src: 'https://github.com/user-attachments/assets/79959017-67c2-4109-98bd-8c1dbba2b34f'
    },
    {
      title: 'Proactive + Translate',
      src: 'https://github.com/user-attachments/assets/c78768be-580e-42e8-a3d8-34eb5f0db6cb'
    }
  ]
]
</script>

<template>
  <section class="home-demo">
    <div class="home-demo__shell">
      <div class="home-demo__header">
        <h2>{{ title }}</h2>
      </div>

      <div v-for="(row, rowIndex) in videos" :key="rowIndex" class="home-demo__grid">
        <article v-for="video in row" :key="video.title" class="home-demo__card">
          <div class="home-demo__label">{{ video.title }}</div>
          <video :src="video.src" controls playsinline preload="metadata" />
        </article>
      </div>
    </div>
  </section>
</template>
