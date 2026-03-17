import api from './index'

export interface LoginData {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface UserInfo {
  id: number
  username: string
  role: string
  created_at: string
  updated_at: string
}

export const loginApi = (data: LoginData) =>
  api.post<TokenResponse>('/auth/login', data)

export const getMeApi = () =>
  api.get<UserInfo>('/auth/me')
