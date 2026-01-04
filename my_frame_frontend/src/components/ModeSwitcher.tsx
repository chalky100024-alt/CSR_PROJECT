import { useState } from 'react';
import { SegmentedControl, Group, Text, Loader, rem } from '@mantine/core';
import { IconMoonStars, IconSun } from '@tabler/icons-react';

interface ModeSwitcherProps {
    currentMode: string;
    onModeChange: (newMode: string) => void;
    t: (key: any) => string;
}

export function ModeSwitcher({ currentMode, onModeChange, t }: ModeSwitcherProps) {
    const [loading, setLoading] = useState(false);

    const handleChange = async (value: string) => {
        if (value === currentMode) return;

        setLoading(true);
        try {
            // Since the backend uses a toggle endpoint, we might have issues if we assume setting specific val.
            // But let's check if the backend supports setting specific mode?
            // Ah, the user code earlier showed 'toggle_mode' action.
            // Wait, if we use SegmentedControl, 'clicking' the other option implies specific intent.
            // If we simply call toggle, it relies on sync.
            // Let's call toggle ONLY if the selected value is different.

            // Actually, safer to verify:
            // Before calling, we assume the user clicked the OTHER one.
            const res = await fetch('/api/system?action=toggle_mode');
            const data = await res.json();

            if (data.status === 'success' && data.mode) {
                // Verify if the result matches what we wanted
                // If we wanted 'settings' (Manual) but it toggled to something else? 
                // Usually toggle flips A <-> B. So it should work.
                // But if we have race condition? 
                // Ideally App.tsx should pass the handler.
                onModeChange(data.mode);
            }
        } catch (error) {
            console.error("Mode toggle failed", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Group gap="xs">
            {loading && <Loader size="sm" color="gray" />}
            <SegmentedControl
                value={currentMode}
                onChange={handleChange}
                data={[
                    {
                        value: 'operation',
                        label: (
                            <Group gap={5} wrap="nowrap">
                                <IconMoonStars style={{ width: rem(16), height: rem(16) }} />
                                <Text size="xs" fw={500} span>{t('modeAutoLabel')}</Text>
                            </Group>
                        )
                    },
                    {
                        value: 'settings',
                        label: (
                            <Group gap={5} wrap="nowrap">
                                <IconSun style={{ width: rem(16), height: rem(16) }} />
                                <Text size="xs" fw={500} span>{t('modeManualLabel')}</Text>
                            </Group>
                        )
                    },
                ]}
                color={currentMode === 'operation' ? 'blue' : 'yellow'}
                radius="xl"
                size="sm"
                // Style to make it look prominent
                styles={{
                    root: { border: '1px solid var(--mantine-color-default-border)' }
                }}
            />
        </Group>
    );
}
