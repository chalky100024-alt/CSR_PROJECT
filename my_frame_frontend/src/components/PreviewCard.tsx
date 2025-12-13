import { useState, useEffect } from 'react';
import { Card, Image, Text, Group, Button, Slider, Stack, Collapse, Badge, AspectRatio } from '@mantine/core';
import { IconDeviceFloppy } from '@tabler/icons-react';
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

        // Confirm completely removed
        await saveConfig(finalConfig, true);
    };

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

            <Card.Section p="md" style={{ background: '#f8f9fa' }}>
                <Stack align="center" justify="center">
                    <div style={{ width: '100%', maxWidth: '600px', margin: '0 auto' }}>
                        <Card shadow="sm" radius="md" p={0} withBorder style={{ overflow: 'hidden' }}>
                            <AspectRatio ratio={800 / 480}>
                                <div style={{
                                    width: '100%',
                                    height: '100%',
                                    display: 'flex',
                                    justifyContent: 'center',
                                    alignItems: 'center',
                                    background: '#e0e0e0',
                                    backgroundImage: 'radial-gradient(#ccc 1px, transparent 1px)',
                                    backgroundSize: '10px 10px'
                                }}>
                                    <Image
                                        src={imgUrl}
                                        alt="E-Paper Preview"
                                        fit="contain"
                                        w="100%"
                                        h="100%"
                                        fallbackSrc="https://placehold.co/800x480?text=Loading+Preview"
                                    />
                                </div>
                            </AspectRatio>
                        </Card>
                        <Text size="xs" c="dimmed" ta="center" mt="xs">
                            Preview (800x480)
                        </Text>
                    </div>
                </Stack>
            </Card.Section>

            <Card.Section inheritPadding pb="md">
                <Button
                    variant="filled"
                    color="blue"
                    radius="md"
                    fullWidth
                    size="md"
                    onClick={handleSaveAndTransfer}
                    loading={transferring}
                    leftSection={<IconDeviceFloppy size={20} />}
                >
                    {t('saveTransfer')}
                </Button>
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

                    <Text size="sm" fw={500} mt="xs">Horizontal Position (X)</Text>
                    <Slider
                        value={config.layout.x ?? 550} // Default approx
                        onChange={(v) => {
                            // Force type to custom when moving slider
                            setConfig({ ...config, layout: { ...config.layout, x: v, type: 'custom' } });
                        }}
                        onChangeEnd={(v) => {
                            // Update both X and Type
                            const newLayout = { ...config.layout, x: v, type: 'custom' };
                            setConfig({ ...config, layout: newLayout });
                            saveConfig({ layout: newLayout }, false).then(() => {
                                // Force refresh logic duplicated from updateLayout
                                let url = `${getPreviewUrl()}&t=${Date.now()}`;
                                const currentPhoto = selectedPhoto || config.selected_photo;
                                if (currentPhoto) url += `&min_filename=${encodeURIComponent(currentPhoto)}`;
                                setImgUrl(url);
                            });
                        }}
                        min={0} max={800} step={10}
                        label={(v) => `${v}px`}
                    />
                </Stack>
            </Collapse>
        </Card>
    );
}
