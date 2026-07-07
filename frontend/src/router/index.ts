import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      redirect: '/files'
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
      path: '/cms/tasks',
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
      redirect: '/review/compare'
    },
    {
      path: '/review/compare',
      name: 'PdfCompareReview',
      component: () => import('../views/CompareReview.vue')
    },
    {
      path: '/review/pdf',
      redirect: '/review/compare'
    },
    {
      path: '/review/outline',
      redirect: '/review/compare'
    },
    {
      path: '/review/standard',
      redirect: '/review/compare'
    },
    {
      path: '/review/final',
      redirect: '/review/compare'
    },
    {
      path: '/review/preview/:id',
      name: 'ReviewPreview',
      redirect: route => ({
        path: '/review/compare',
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

export default router 
