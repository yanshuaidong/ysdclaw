import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Login.vue'),
    },
    {
      path: '/',
      component: () => import('../layouts/DashboardLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: '/products',
        },
        {
          path: 'users',
          name: 'UserManagement',
          component: () => import('../views/UserManagement.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'products',
          name: 'ProductBrowse',
          component: () => import('../views/ProductBrowse.vue'),
        },
      ],
    },
  ],
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  if (to.path === '/login') {
    if (authStore.isLoggedIn) {
      next('/')
    } else {
      next()
    }
    return
  }

  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next('/login')
    return
  }

  if (authStore.isLoggedIn && !authStore.userInfo) {
    try {
      await authStore.fetchUserInfo()
    } catch {
      authStore.logout()
      next('/login')
      return
    }
  }

  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next('/products')
    return
  }

  next()
})

export default router
