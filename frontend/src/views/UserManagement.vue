<template>
  <div>
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">
        新增用户
      </el-button>
    </div>

    <el-table :data="users" v-loading="tableLoading" stripe border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="role" label="角色" width="120">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">
            {{ row.role === 'admin' ? '管理员' : '普通用户' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" text @click="openEditDialog(row)">
            编辑
          </el-button>
          <el-popconfirm
            title="确定删除该用户吗？"
            @confirm="handleDelete(row.id)"
          >
            <template #reference>
              <el-button
                size="small"
                type="danger"
                text
                :disabled="row.id === authStore.userInfo?.id"
              >
                删除
              </el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑用户' : '新增用户'"
      width="460px"
      destroy-on-close
    >
      <el-form
        ref="dialogFormRef"
        :model="dialogForm"
        :rules="dialogRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="dialogForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" :prop="isEditing ? '' : 'password'">
          <el-input
            v-model="dialogForm.password"
            type="password"
            :placeholder="isEditing ? '留空则不修改密码' : '请输入密码'"
            show-password
          />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="dialogForm.role" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { getUsersApi, createUserApi, updateUserApi, deleteUserApi, type User } from '../api/user'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const users = ref<User[]>([])
const tableLoading = ref(false)
const dialogVisible = ref(false)
const submitLoading = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const dialogFormRef = ref<FormInstance>()

const dialogForm = reactive({
  username: '',
  password: '',
  role: 'user',
})

const dialogRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

async function fetchUsers() {
  tableLoading.value = true
  try {
    const res = await getUsersApi()
    users.value = res.data
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '获取用户列表失败')
  } finally {
    tableLoading.value = false
  }
}

function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  dialogForm.username = ''
  dialogForm.password = ''
  dialogForm.role = 'user'
  dialogVisible.value = true
}

function openEditDialog(user: User) {
  isEditing.value = true
  editingId.value = user.id
  dialogForm.username = user.username
  dialogForm.password = ''
  dialogForm.role = user.role
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await dialogFormRef.value?.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    if (isEditing.value && editingId.value !== null) {
      const data: Record<string, string> = {
        username: dialogForm.username,
        role: dialogForm.role,
      }
      if (dialogForm.password) {
        data.password = dialogForm.password
      }
      await updateUserApi(editingId.value, data)
      ElMessage.success('修改成功')
    } else {
      await createUserApi(dialogForm)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchUsers()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await deleteUserApi(id)
    ElMessage.success('删除成功')
    fetchUsers()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
}

onMounted(fetchUsers)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}
</style>
