import axios from 'axios';

const api = axios.create({
    baseURL: '/', // Proxied to :8080 by Vite
});

export interface PhotoConfig {
    layout: {
        widget_size: number;
        font_size: number;
        opacity: number;
        position: string;
        x?: number;
        y?: number;
        type?: string;
    };
    location?: { name: string; nx: number; ny: number };
    ai_provider?: string;
    api_key_hf?: string;
    api_key_google?: string;
    google_project_id?: string;
    google_location?: string;
    selected_photo?: string;
    [key: string]: any;
}

export const fetchPhotos = async (): Promise<string[]> => {
    const res = await api.get('/api/list_photos');
    return res.data;
};

export const uploadPhoto = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post('/upload', formData);
    return res.data;
};

export const deletePhotos = async (filenames: string[]) => {
    const res = await api.post('/api/delete_photos', { filenames });
    return res.data;
};

export const generateAI = async (prompt: string, style: string, imageFilenames?: string[]) => {
    const res = await api.post('/api/generate_ai', { prompt, style, image_filenames: imageFilenames });
    return res.data; // { status: "success", image: "..." }
};

export const getConfig = async (): Promise<PhotoConfig> => {
    const res = await api.get(`/api/get_config?t=${Date.now()}`);
    return res.data;
};

export const saveConfig = async (config: Partial<PhotoConfig>, refresh = false) => {
    const res = await api.post(`/api/save_config?refresh=${refresh}`, config);
    return res.data;
};

export const getPreviewUrl = () => `/api/preview?t=${Date.now()}`;
export const getPhotoUrl = (filename: string) => `/uploads/${filename}`;

// Settings APIs
export const searchLocation = async (query: string): Promise<{ name: string; nx: number; ny: number }[]> => {
    const res = await api.get(`/api/search_location?q=${encodeURIComponent(query)}`);
    return res.data;
};

export const scanWifi = async (): Promise<{ ssid: string; signal: number }[]> => {
    const res = await api.get('/api/wifi_scan');
    return res.data;
};

export const getBatteryStatus = async (): Promise<{ level: number; charging: boolean }> => {
    const res = await api.get('/api/battery');
    return res.data;
};

export const connectWifi = async (ssid: string, password: string) => {
    const res = await api.post('/api/wifi_connect', { ssid, password });
    return res.data;
};

export const systemAction = async (action: 'reboot' | 'shutdown' | 'update') => {
    const res = await api.get(`/api/system?action=${action}`);
    return res.data;
};
