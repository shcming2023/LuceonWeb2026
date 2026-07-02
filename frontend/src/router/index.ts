import { createRouter, createWebHistory } from 'vue-router'
import { ensureCurrentUser, fetchCurrentUser, getCurrentUser } from '@/utils/user'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Login.vue'),
      meta: { public: true }
    },
    {
      path: '/',
      name: 'Home',
      component: () => import('../views/Home.vue')
    },
    {
      path: '/upload',
      name: 'Upload',
      redirect: '/files'
    },
    {
      path: '/files',
      name: 'Files',
      component: () => import('../views/Files.vue')
    },
    {
      path: '/files/preview/:id',
      name: 'FilePreview',
      component: () => import('../views/FilePreview.vue'),
      props: route => ({
        fileId: route.params.id,
        page: Number(route.query.page) || 1
      })
    },
    {
      path: '/review',
      name: 'Review',
      redirect: '/review/pdf'
    },
    {
      path: '/review/pdf',
      name: 'PdfParseReview',
      component: () => import('../views/Review.vue'),
      meta: { reviewMode: 'page' }
    },
    {
      path: '/review/outline',
      name: 'OutlineRebuildReview',
      component: () => import('../views/Review.vue'),
      meta: { reviewMode: 'outline' }
    },
    {
      path: '/review/standard',
      name: 'StandardOutputReview',
      component: () => import('../views/Review.vue'),
      meta: { reviewMode: 'standard' }
    },
    {
      path: '/review/final',
      name: 'StandardQualityReview',
      component: () => import('../views/FinalReview.vue')
    },
    {
      path: '/review/preview/:id',
      name: 'ReviewPreview',
      redirect: route => ({
        path: route.query.outline === '1' ? '/review/outline' : '/review/pdf',
        query: {
          asset_id: String(route.params.id)
        }
      })
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('../views/Settings.vue')
    }
  ]
})

router.beforeEach(async (to) => {
  if (to.meta.public) {
    if (getCurrentUser()) {
      return { path: '/' }
    }
    try {
      await fetchCurrentUser()
      return { path: '/' }
    } catch {
      return true
    }
  }

  try {
    await ensureCurrentUser()
    return true
  } catch {
    return {
      path: '/login',
      query: { redirect: to.fullPath }
    }
  }
})

export default router 
