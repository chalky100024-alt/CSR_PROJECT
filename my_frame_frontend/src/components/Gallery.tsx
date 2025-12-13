import { useState, useEffect } from 'react';
import { SimpleGrid, Card, Image, Button, Group, Text, FileButton, LoadingOverlay } from '@mantine/core';
import { IconTrash, IconUpload, IconCheck } from '@tabler/icons-react';
import { fetchPhotos, deletePhotos, uploadPhoto, getPhotoUrl } from '../api';
import { useLanguage } from '../context/LanguageContext';

interface GalleryProps {
    selectedPhoto: string;
    onSelectPhoto: (photo: string) => void;
}

export function Gallery({ selectedPhoto, onSelectPhoto }: GalleryProps) {
    const { t } = useLanguage();
    const [photos, setPhotos] = useState<string[]>([]);
    const [deleteMode, setDeleteMode] = useState(false);
    const [selectedForDelete, setSelectedForDelete] = useState<Set<string>>(new Set());
    const [uploading, setUploading] = useState(false);
    const [loading, setLoading] = useState(false);

    const loadPhotos = async () => {
        setLoading(true);
        const list = await fetchPhotos();
        setPhotos(list);
        setLoading(false);
    };

    useEffect(() => { loadPhotos(); }, []);

    const handleUpload = async (file: File | null) => {
        if (!file) return;
        setUploading(true);
        await uploadPhoto(file);
        await loadPhotos();
        setUploading(false);
    };

    const toggleDeleteSelection = (photo: string) => {
        const newSet = new Set(selectedForDelete);
        if (newSet.has(photo)) newSet.delete(photo);
        else newSet.add(photo);
        setSelectedForDelete(newSet);
    };

    const handleDelete = async () => {
        if (selectedForDelete.size === 0) return;
        if (!confirm('Are you sure?')) return;

        await deletePhotos(Array.from(selectedForDelete));
        setDeleteMode(false);
        setSelectedForDelete(new Set());
        loadPhotos();
    };

    return (
        <Card shadow="sm" radius="md" withBorder>
            <LoadingOverlay visible={loading || uploading} zIndex={1000} overlayProps={{ radius: "sm", blur: 2 }} />
            <Group justify="space-between" mb="md">
                <Text fw={700} size="lg">{t('galleryTitle')}</Text>
                <Group>
                    <FileButton onChange={handleUpload} accept="image/png,image/jpeg,image/heic">
                        {(props) => <Button {...props} size="xs" variant="light" leftSection={<IconUpload size={14} />}>{t('uploadBtn')}</Button>}
                    </FileButton>
                    <Button
                        size="xs"
                        color={deleteMode ? 'red' : 'gray'}
                        variant={deleteMode ? 'filled' : 'outline'}
                        leftSection={<IconTrash size={14} />}
                        onClick={() => setDeleteMode(!deleteMode)}
                    >
                        {deleteMode ? t('cancel') : t('deleteMode')}
                    </Button>
                </Group>
            </Group>

            {deleteMode && (
                <Button fullWidth color="red" mb="md" disabled={selectedForDelete.size === 0} onClick={handleDelete}>
                    {t('deleteSelected')} ({selectedForDelete.size})
                </Button>
            )}

            <SimpleGrid cols={{ base: 3, sm: 4 }} spacing="xs">
                {photos.map(photo => {
                    const isSelected = selectedPhoto === photo;
                    const isMarked = selectedForDelete.has(photo);

                    return (
                        <Card
                            key={photo}
                            p={0}
                            radius="sm"
                            style={{
                                cursor: 'pointer',
                                border: deleteMode
                                    ? (isMarked ? '3px solid red' : 'none')
                                    : (isSelected ? '3px solid #007AFF' : 'none'),
                                opacity: deleteMode && !isMarked ? 0.6 : 1
                            }}
                            onClick={() => deleteMode ? toggleDeleteSelection(photo) : onSelectPhoto(photo)}
                        >
                            <Image src={getPhotoUrl(photo)} h={100} fit="cover" />
                            {deleteMode && isMarked && (
                                <div style={{ position: 'absolute', top: 5, right: 5, background: 'red', borderRadius: '50%', padding: 2 }}>
                                    <IconCheck color="white" size={12} />
                                </div>
                            )}
                        </Card>
                    );
                })}
            </SimpleGrid>

            {photos.length === 0 && !loading && <Text c="dimmed" ta="center" py="xl">No photos yet.</Text>}
        </Card>
    );
}
