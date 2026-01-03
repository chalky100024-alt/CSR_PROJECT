import { useState, useEffect } from 'react';
import { SimpleGrid, Card, Image, Button, Group, Text, FileButton, LoadingOverlay } from '@mantine/core';
import { IconTrash, IconUpload, IconCheck } from '@tabler/icons-react';
import { fetchPhotos, deletePhotos, uploadPhoto, getPhotoUrl } from '../api';
import { useLanguage } from '../context/LanguageContext';

interface GalleryProps {
    selectedPhoto: string;
    onSelectPhoto: (photo: string) => void;
    // [Shuffle Props]
    shuffleMode: boolean;
    shufflePlaylist: string[];
    onToggleShuffle: (enabled: boolean) => void;
    onUpdatePlaylist: (playlist: string[]) => void;
}

export function Gallery({ selectedPhoto, onSelectPhoto, shuffleMode, shufflePlaylist, onToggleShuffle, onUpdatePlaylist }: GalleryProps) {
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

    const togglePlaylistSelection = (photo: string) => {
        const currentList = new Set(shufflePlaylist);
        if (currentList.has(photo)) currentList.delete(photo);
        else currentList.add(photo);
        onUpdatePlaylist(Array.from(currentList));
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
                    {/* Shuffle Toggle */}
                    <Button
                        size="xs"
                        variant={shuffleMode ? "filled" : "light"}
                        color={shuffleMode ? "violet" : "gray"}
                        onClick={() => onToggleShuffle(!shuffleMode)}
                    >
                        {shuffleMode ? "🔀 Shuffle ON" : "➡️ Shuffle OFF"}
                    </Button>

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

            {shuffleMode && !deleteMode && (
                <Text size="sm" c="violet" mb="xs" fw={500}>
                    Select photos for random shuffle ({shufflePlaylist.length} selected)
                </Text>
            )}

            <SimpleGrid cols={{ base: 3, sm: 4 }} spacing="xs">
                {photos.map(photo => {
                    // Logic depends on Mode
                    let isSelected = false;

                    if (deleteMode) {
                        isSelected = selectedForDelete.has(photo);
                    } else if (shuffleMode) {
                        isSelected = shufflePlaylist.includes(photo);
                    } else {
                        isSelected = selectedPhoto === photo;
                    }

                    return (
                        <Card
                            key={photo}
                            p={0}
                            radius="sm"
                            style={{
                                cursor: 'pointer',
                                border: isSelected
                                    ? (deleteMode ? '3px solid red' : (shuffleMode ? '3px solid violet' : '3px solid #007AFF'))
                                    : 'none',
                                opacity: deleteMode && !isSelected ? 0.6 : 1,
                                position: 'relative'
                            }}
                            onClick={() => {
                                if (deleteMode) toggleDeleteSelection(photo);
                                else if (shuffleMode) togglePlaylistSelection(photo);
                                else onSelectPhoto(photo);
                            }}
                        >
                            <Image src={getPhotoUrl(photo)} h={100} fit="cover" />
                            {/* Checkmark Badge */}
                            {isSelected && (
                                <div style={{
                                    position: 'absolute', top: 5, right: 5,
                                    background: deleteMode ? 'red' : (shuffleMode ? 'violet' : '#007AFF'),
                                    borderRadius: '50%', padding: 2, display: 'flex'
                                }}>
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
