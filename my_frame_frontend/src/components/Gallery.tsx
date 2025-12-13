import { useState, useEffect, useRef } from 'react';
import { SimpleGrid, Card, Image, ActionIcon, Button, Group, Text, FileButton, Transition, LoadingOverlay } from '@mantine/core';
import { IconTrash, IconUpload, IconCheck, IconX } from '@tabler/icons-react';
import { fetchPhotos, deletePhotos, uploadPhoto, getPhotoUrl } from '../api';

interface GalleryProps {
    onSelectPhoto: (photo: string) => void;
    selectedPhoto: string;
}

export function Gallery({ onSelectPhoto, selectedPhoto }: GalleryProps) {
    const [photos, setPhotos] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);

    // Delete Mode State
    const [deleteMode, setDeleteMode] = useState(false);
    const [selectedForDelete, setSelectedForDelete] = useState<Set<string>>(new Set());

    const loadPhotos = async () => {
        setLoading(true);
        try {
            const list = await fetchPhotos();
            setPhotos(list);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadPhotos();
    }, []);

    const handleUpload = async (file: File | null) => {
        if (!file) return;
        setLoading(true);
        try {
            await uploadPhoto(file);
            await loadPhotos();
        } catch (e) {
            alert("Upload failed");
        } finally {
            setLoading(false);
        }
    };

    const toggleSelection = (photo: string) => {
        const next = new Set(selectedForDelete);
        if (next.has(photo)) next.delete(photo);
        else next.add(photo);
        setSelectedForDelete(next);
    };

    const executeDelete = async () => {
        if (!confirm(`Delete ${selectedForDelete.size} photos?`)) return;
        setLoading(true);
        try {
            await deletePhotos(Array.from(selectedForDelete));
            setSelectedForDelete(new Set());
            setDeleteMode(false);
            await loadPhotos();
        } catch (e) {
            alert("Delete failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card shadow="sm" radius="md" withBorder>
            <LoadingOverlay visible={loading} />

            <Group justify="space-between" mb="md">
                <Text fw={700} size="lg">My Photos</Text>
                <Group gap="xs">
                    {!deleteMode ? (
                        <>
                            <FileButton onChange={handleUpload} accept="image/png,image/jpeg">
                                {(props) => <Button {...props} variant="light" leftSection={<IconUpload size={16} />}>Upload</Button>}
                            </FileButton>
                            <Button variant="subtle" color="red" leftSection={<IconTrash size={16} />} onClick={() => setDeleteMode(true)}>
                                Select
                            </Button>
                        </>
                    ) : (
                        <>
                            <Button variant="subtle" onClick={() => { setDeleteMode(false); setSelectedForDelete(new Set()); }}>Cancel</Button>
                            <Button color="red" disabled={selectedForDelete.size === 0} onClick={executeDelete}>
                                Delete ({selectedForDelete.size})
                            </Button>
                        </>
                    )}
                </Group>
            </Group>

            <SimpleGrid cols={{ base: 2, sm: 3, md: 4 }} spacing="xs">
                {photos.map((photo) => {
                    const isSelected = selectedPhoto === photo;
                    const isMarkedDelete = selectedForDelete.has(photo);

                    return (
                        <div
                            key={photo}
                            style={{ position: 'relative', cursor: 'pointer' }}
                            onClick={() => {
                                if (deleteMode) toggleSelection(photo);
                                else onSelectPhoto(photo);
                            }}
                        >
                            <Image
                                src={getPhotoUrl(photo)}
                                radius="md"
                                h={120}
                                fit="cover"
                                style={{
                                    border: deleteMode
                                        ? (isMarkedDelete ? '4px solid #fa5252' : 'none')
                                        : (isSelected ? '4px solid #228be6' : 'none'),
                                    opacity: deleteMode && isMarkedDelete ? 0.6 : 1,
                                    transition: 'all 0.2s ease'
                                }}
                            />
                            {deleteMode && isMarkedDelete && (
                                <IconCheck
                                    style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: 'white', filter: 'drop-shadow(0 0 4px rgba(0,0,0,0.5))' }}
                                    size={40}
                                />
                            )}
                        </div>
                    );
                })}
            </SimpleGrid>

            {photos.length === 0 && !loading && <Text c="dimmed" ta="center" py="xl">No photos yet.</Text>}
        </Card>
    );
}
