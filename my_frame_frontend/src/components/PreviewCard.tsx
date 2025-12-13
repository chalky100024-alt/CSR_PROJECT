import { useState, useEffect } from 'react';
import { Card, Image, Text, Group, Button, Slider, Stack, Collapse } from '@mantine/core';
import { IconSettings } from '@tabler/icons-react';
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
        // Force refresh preview image with new timestamp
        setImgUrl(`${getPreviewUrl()}&t=${Date.now()}`);
    };

    const handleSaveAndTransfer = async () => {
        // Create final config merging current local state with the authoritative selectedPhoto
        const finalConfig = {
            ...config,
            selected_photo: selectedPhoto || config.selected_photo
        };

        await saveConfig(finalConfig, true);
        alert(t('saveTransfer') + " OK!");
    };

    return (
        <Card shadow="sm" radius="md" withBorder>
            <Group justify="space-between" mb="xs">
                <Text fw={700} size="lg" c="blue">{t('previewTitle')}</Text>
                <Button variant="subtle" size="xs" leftSection={<IconSettings size={14} />} onClick={() => setOpenControls(!openControls)}>
                    {t('previewEdit')}
                </Button>
            </Group>

            <div style={{
                background: '#eee',
                borderRadius: 8,
                overflow: 'hidden',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                aspectRatio: '800/480',
                width: '100%',
                maxWidth: 800,
                margin: '0 auto'
            }}>
                <Image src={imgUrl} w="100%" h="100%" fit="contain" />
            </div>

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

            <Button fullWidth mt="md" onClick={handleSaveAndTransfer} variant="filled">
                {t('saveTransfer')}
            </Button>
        </Card>
    );
}
