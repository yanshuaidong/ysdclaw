import api from './index'

export interface User {
  id: number
  username: string
  role: string
  created_at: string
  updated_at: string
}

export interface UserCreateData {
  username: string
  password: string
  role: string
}

export interface UserUpdateData {
  username?: string
  password?: string
  role?: string
}

export const getUsersApi = () =>
  api.get<User[]>('/users')

export const createUserApi = (data: UserCreateData) =>
  api.post<User>('/users', data)

export const updateUserApi = (id: number, data: UserUpdateData) =>
  api.put<User>(`/users/${id}`, data)

export const deleteUserApi = (id: number) =>
  api.delete(`/users/${id}`)
