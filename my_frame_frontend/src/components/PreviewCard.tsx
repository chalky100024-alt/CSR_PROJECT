import { useState, useEffect } from 'react';
import { Card, Image, Text, Group, Button, Slider, Stack, Collapse, Badge, Loader } from '@mantine/core';
import { IconSettings, IconRefresh, IconDeviceFloppy } from '@tabler/icons-react';
import { getPreviewUrl, saveConfig, getConfig } from '../api';
import { useLanguage } from '../context/LanguageContext';

interface PreviewCardProps {
    refreshKey: number;
    selectedPhoto?: string;
}

export function PreviewCard({ refreshKey, selectedPhoto }: PreviewCardProps) {
    const { t } = useLanguage();
    const [imgUrl, setImgUrl] = useState(getPreviewUrl());
    const [config, setConfig] = useState<any>({ layout: { widget_size: 1.0, opacity: 0.6 } });
    const [openControls, setOpenControls] = useState(false);

    useEffect(() => {
        let url = getPreviewUrl();
        // If selectedPhoto is provided, force it in URL to update instantly
        if (selectedPhoto) {
            url += `&min_filename=${encodeURIComponent(selectedPhoto)}`;
        }
        setImgUrl(url);
    }, [refreshKey, selectedPhoto]);

    useEffect(() => {
        getConfig().then(setConfig);
    }, [refreshKey]);

    const updateLayout = async (key: string, val: number) => {
        const newLayout = { ...config.layout, [key]: val };
        setConfig({ ...config, layout: newLayout });
        await saveConfig({ layout: newLayout }, false);

        // Force refresh preview image with new timestamp AND preserve selected photo
        let url = `${getPreviewUrl()}&t=${Date.now()}`;
        const currentPhoto = selectedPhoto || config.selected_photo;
        if (currentPhoto) {
            url += `&min_filename=${encodeURIComponent(currentPhoto)}`;
        }
        setImgUrl(url);
    };

    const handleSaveAndTransfer = async () => {
        console.log("saveTransfer clicked. selectedPhoto prop:", selectedPhoto);
        console.log("saveTransfer config state:", config);

        // Explicitly choose photo
        const photoToSave = selectedPhoto || config.selected_photo;

        // Create final config
        const finalConfig = {
            ...config,
            selected_photo: photoToSave
        };

        // Debug Alert for User
        const msg = `Saving Layout & Transferring:\nPhoto: ${photoToSave}\nWidget Size: ${config.layout.widget_size}`;
        if (!confirm(msg)) return; // Allow user to cancel if wrong

        await saveConfig(finalConfig, true);
        alert(t('saveTransfer') + " OK!");
    };
    const handleRefresh = () => {
        setImgUrl(getPreviewUrl() + '&t=' + Date.now());
    };

    const loading = false; // Placeholder if not strictly tracked, or use derived state
    const transferring = false; // Placeholder

    return (
        <Card
            shadow="lg"
            padding="xl"
            radius="xl"
            withBorder
            style={{
                height: '100%',
                background: 'rgba(255, 255, 255, 0.8)',
                backdropFilter: 'blur(20px)',
                display: 'flex',
                flexDirection: 'column'
            }}
        >
            <Card.Section withBorder inheritPadding py="xs" style={{ borderBottom: '1px solid rgba(0,0,0,0.05)' }}>
                <Group justify="space-between">
                    <Text fw={600} size="lg" style={{ fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif' }}>
                        {t('previewTitle')}
                    </Text>
                    <Badge color="green" variant="light">Active</Badge>
                </Group>
            </Card.Section>

            <Card.Section mt="md" mb="md" style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%', position: 'relative' }}>
                <div style={{
                    position: 'relative',
                    borderRadius: '12px',
                    overflow: 'hidden',
                    boxShadow: '0 8px 16px rgba(0,0,0,0.1)',
                    background: 'white'
                }}>
                    <Image
                        src={imgUrl}
                        alt="E-Paper Preview"
                        fit="contain"
                        w="auto"
                        h={300} // Fixed height for consistency
                        fallbackSrc="https://placehold.co/800x480?text=Loading+Preview"
                    />
                </div>
            </Card.Section>

            <Card.Section inheritPadding pb="md">
                <Group grow>
                    <Button
                        variant="light"
                        color="blue"
                        radius="md"
                        onClick={handleRefresh}
                        loading={loading}
                        leftSection={<IconRefresh size={18} />}
                    >
                        {t('refresh')}
                    </Button>
                    <Button
                        variant="filled"
                        color="blue"
                        radius="md"
                        onClick={handleSaveAndTransfer}
                        loading={transferring}
                        leftSection={<IconDeviceFloppy size={18} />}
                    >
                        {t('saveTransfer')}
                    </Button>
                </Group>
            </Card.Section>

            {/* Hidden Controls Toggle for Advanced Settings (optional) */}
            <Group justify="center" mt="xs">
                <Button variant="subtle" size="xs" color="gray" onClick={() => setOpenControls(!openControls)}>
                    {openControls ? "Hide Options" : "Show Options"}
                </Button>
            </Group>

            <Collapse in={openControls}>
                <Stack mt="md" gap="xs">
                    <Text size="sm" fw={500}>{t('widgetSize')}</Text>
                    <Slider
                        value={config.layout.widget_size}
                        onChange={(v) => {
                            setConfig({ ...config, layout: { ...config.layout, widget_size: v } });
                        }}
                        onChangeEnd={(v) => updateLayout('widget_size', v)}
                        min={0.5} max={2.0} step={0.1}
                        label={(v) => `${v}x`}
                    />
                    <Text size="sm" fw={500} mt="xs">{t('opacity')}</Text>
                    <Slider
                        value={config.layout.opacity}
                        onChange={(v) => {
                            setConfig({ ...config, layout: { ...config.layout, opacity: v } });
                        }}
                        onChangeEnd={(v) => updateLayout('opacity', v)}
                        min={0.0} max={1.0} step={0.1}
                        label={(v) => `${Math.round(v * 100)}%`}
                    />
                </Stack>
            </Collapse>
        </Card>
    );
}
