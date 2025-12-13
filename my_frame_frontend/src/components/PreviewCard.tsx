import { useState, useEffect } from 'react';
import { Card, Image, Text, Group, Button, Slider, Stack, Collapse } from '@mantine/core';
import { IconDeviceTv, IconSettings } from '@tabler/icons-react';
import { getPreviewUrl, saveConfig, getConfig } from '../api';

interface PreviewCardProps {
    refreshKey: number; // Increment to force reload
}

export function PreviewCard({ refreshKey }: PreviewCardProps) {
    // We append a timestamp to the image URL to force browser refresh
    const [imgUrl, setImgUrl] = useState(getPreviewUrl());
    const [config, setConfig] = useState<any>({ layout: { widget_size: 1.0, opacity: 0.6 } });
    const [openControls, setOpenControls] = useState(false);

    useEffect(() => {
        setImgUrl(getPreviewUrl()); // Refresh image when key changes
    }, [refreshKey]);

    useEffect(() => {
        getConfig().then(setConfig);
    }, []);

    const updateLayout = async (key: string, val: number) => {
        const newLayout = { ...config.layout, [key]: val };
        setConfig({ ...config, layout: newLayout });
        // Debounce saving could be better, but for now simple save
        // We don't refresh display on every slider move, too slow
        await saveConfig({ layout: newLayout }, false);
    };

    const handleSaveAndTransfer = async () => {
        await saveConfig(config, true); // True triggers E-Ink Refresh
        alert("Transferred to Frame!");
    };

    return (
        <Card shadow="sm" radius="md" withBorder>
            <Group justify="space-between" mb="xs">
                <Text fw={700} size="lg" c="appleBlue">Live Preview</Text>
                <Button variant="subtle" size="xs" leftSection={<IconSettings size={14} />} onClick={() => setOpenControls(!openControls)}>
                    Adjust Widgets
                </Button>
            </Group>

            <div style={{ background: '#eee', borderRadius: 8, overflow: 'hidden', display: 'flex', justifyContent: 'center' }}>
                <Image src={imgUrl} fit="contain" style={{ maxHeight: 400 }} />
            </div>

            <Collapse in={openControls}>
                <Stack mt="md" gap="xs">
                    <Text size="sm" fw={500}>Widget Size</Text>
                    <Slider
                        value={config.layout.widget_size}
                        onChange={(v) => updateLayout('widget_size', v)}
                        min={0.5} max={2.0} step={0.1}
                        label={(v) => `${v}x`}
                    />

                    <Text size="sm" fw={500} mt="xs">Opacity</Text>
                    <Slider
                        value={config.layout.opacity}
                        onChange={(v) => updateLayout('opacity', v)}
                        min={0.0} max={1.0} step={0.1}
                        label={(v) => `${Math.round(v * 100)}%`}
                    />
                </Stack>
            </Collapse>

            <Button fullWidth mt="md" onClick={handleSaveAndTransfer} variant="filled">
                Save Layout & Transfer to Frame
            </Button>
        </Card>
    );
}
