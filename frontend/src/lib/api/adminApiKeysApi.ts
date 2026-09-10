import { apiClient } from '@/lib/api/client';

export interface ApiKeysStatus {
  youtube: { configured: boolean };
  udemy: { configured: boolean; configured_by: string | null; configured_at: string | null };
}

export async function getApiKeysStatus(): Promise<ApiKeysStatus> {
  const response = await apiClient.get<ApiKeysStatus>('/api/admin/api-keys');
  return response.data;
}

export async function saveYoutubeKey(key: string): Promise<void> {
  await apiClient.put('/api/admin/api-keys/youtube', { key });
}

export async function removeYoutubeKey(): Promise<void> {
  await apiClient.delete('/api/admin/api-keys/youtube');
}

export async function saveUdemyCredential(clientId: string, clientSecret: string): Promise<void> {
  await apiClient.put('/api/admin/api-keys/udemy', { client_id: clientId, client_secret: clientSecret });
}

export async function removeUdemyCredential(): Promise<void> {
  await apiClient.delete('/api/admin/api-keys/udemy');
}
