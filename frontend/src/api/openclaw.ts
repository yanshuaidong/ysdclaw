import axios from 'axios'

const client = axios.create({
  baseURL: '/openclaw-data',
  timeout: 15000,
})

export interface DirEntry {
  name: string
  type: 'file' | 'directory'
  mtime: string
  size: number
}

export async function listDir(path: string): Promise<DirEntry[]> {
  const url = path.endsWith('/') ? path : path + '/'
  const { data } = await client.get<DirEntry[]>(url)
  return data
}

export async function fetchJson<T = any>(path: string): Promise<T> {
  const { data } = await client.get<T>(path)
  return data
}

export async function fetchText(path: string): Promise<string> {
  const { data } = await client.get(path, { responseType: 'text' })
  return data
}
