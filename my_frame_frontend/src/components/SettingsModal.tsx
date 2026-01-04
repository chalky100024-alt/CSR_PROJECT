import { useState, useEffect } from 'react';
import {
    Modal, Tabs, TextInput, Button, Group, Stack, Text,
    Select, PasswordInput, ScrollArea, Textarea, Divider, Loader
} from '@mantine/core';
import { IconMapPin, IconKey, IconDeviceDesktop, IconRefresh, IconCircleCheck, IconAlertCircle } from '@tabler/icons-react';
import { getConfig, saveConfig, searchLocation, scanWifi, connectWifi, systemAction } from '../api';
import { useLanguage } from '../context/LanguageContext';
import type { Language } from '../translations';

interface SettingsModalProps {
    opened: boolean;
    onClose: () => void;
}

export function SettingsModal({ opened, onClose }: SettingsModalProps) {
    const { t, language, setLanguage } = useLanguage();
    const [activeTab, setActiveTab] = useState<string | null>('general');
    const [config, setConfig] = useState<any>({});

    // Location Search
    const [locQuery, setLocQuery] = useState('');
    const [locResults, setLocResults] = useState<any[]>([]);

    // Wifi
    const [networks, setNetworks] = useState<any[]>([]);
    const [wifiPass, setWifiPass] = useState('');
    const [selectedWifi, setSelectedWifi] = useState<string | null>(null);

    useEffect(() => {
        if (opened) getConfig().then(setConfig);
    }, [opened]);

    const handleSave = async () => {
        await saveConfig(config);
        alert(t('saveChanges') + " OK!");
        onClose();
    };

    const handleSearchLoc = async () => {
        if (locQuery.length < 2) return;
        const res = await searchLocation(locQuery);
        setLocResults(res);
    };

    const handleSelectLoc = (loc: any) => {
        setConfig({ ...config, location: loc });
        setLocResults([]);
        setLocQuery('');
    };

    const handleWifiScan = async () => {
        setNetworks([]);
        try {
            const res = await scanWifi();
            setNetworks(res);
        } catch (e) {
            alert(t('scanFailed'));
        }
    };

    const handleWifiConnect = async () => {
        if (!selectedWifi) return;
        await connectWifi(selectedWifi, wifiPass);
        alert(t('connect') + "...");
    };

    // Update State
    const [updateStatus, setUpdateStatus] = useState<'idle' | 'loading' | 'success' | 'uptodate' | 'error'>('idle');
    const [updateMsg, setUpdateMsg] = useState('');

    const handleUpdate = async () => {
        setUpdateStatus('loading');
        try {
            const res = await systemAction('update');
            await new Promise(r => setTimeout(r, 1000)); // Short wait

            if (res && res.status === 'success') {
                setUpdateStatus('success');
                setUpdateMsg(res.message);
            } else if (res && res.status === 'uptodate') {
                setUpdateStatus('uptodate');
                setUpdateMsg(res.message);
            } else {
                setUpdateStatus('error');
                setUpdateMsg(res?.message || 'Unknown error');
            }
        } catch (e: any) {
            setUpdateStatus('error');
            setUpdateMsg(e.toString());
        }
    };

    return (
        <Modal opened={opened} onClose={onClose} title={t('settingsTitle')} size="lg">
            <Tabs value={activeTab} onChange={setActiveTab}>
                <Tabs.List>
                    <Tabs.Tab value="general" leftSection={<IconMapPin size={14} />}>{t('tabGeneral')}</Tabs.Tab>
                    <Tabs.Tab value="api" leftSection={<IconKey size={14} />}>{t('tabApi')}</Tabs.Tab>
                    <Tabs.Tab value="system" leftSection={<IconDeviceDesktop size={14} />}>{t('tabSystem')}</Tabs.Tab>
                </Tabs.List>

                <Tabs.Panel value="general" pt="md">
                    <Stack>
                        <TextInput
                            label={t('currentLoc')}
                            value={config.location?.name || t('notSet')}
                            readOnly
                            rightSection={<IconMapPin size={16} />}
                        />

                        <Select
                            label={t('language')}
                            data={[
                                { value: 'ko', label: '🇰🇷 한국어' },
                                { value: 'en', label: '🇺🇸 English' },
                                { value: 'ja', label: '🇯🇵 日本語' },
                                { value: 'zh', label: '🇨🇳 中文' },
                            ]}
                            value={language}
                            onChange={(v) => setLanguage(v as Language)}
                            allowDeselect={false}
                        />

                        <Group align="flex-end">
                            <TextInput
                                label={t('searchLoc')}
                                placeholder={t('searchLocPlaceholder')}
                                value={locQuery}
                                onChange={(e) => setLocQuery(e.currentTarget.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSearchLoc()}
                                style={{ flex: 1 }}
                            />
                            <Button onClick={handleSearchLoc}>{t('searchBtn')}</Button>
                        </Group>

                        {locResults.length > 0 && (
                            <ScrollArea h={150} type="always" offsetScrollbars>
                                <Stack gap="xs">
                                    {locResults.map((loc, idx) => (
                                        <Button key={idx} variant="light" justify="start" onClick={() => handleSelectLoc(loc)}>
                                            {loc.name}
                                        </Button>
                                    ))}
                                </Stack>
                            </ScrollArea>
                        )}
                    </Stack>
                </Tabs.Panel>

                <Tabs.Panel value="api" pt="md">
                    <Stack>
                        <Text fw={700} c="dimmed" size="sm" tt="uppercase">{t('imageGeneration')}</Text>

                        <Group align="flex-start" grow>
                            <TextInput
                                label={t('hfApiToken')}
                                placeholder="hf_..."
                                value={config.api_key_hf || ''}
                                onChange={(e) => setConfig({ ...config, api_key_hf: e.currentTarget.value })}
                            />
                        </Group>

                        <Stack gap="xs" mt="sm">
                            <Text size="sm" fw={500}>{t('googleVertexAi')}</Text>
                            <Group grow>
                                <TextInput
                                    label={t('projectId')}
                                    placeholder="my-project-id"
                                    value={config.google_project_id || ''}
                                    onChange={(e) => setConfig({ ...config, google_project_id: e.currentTarget.value })}
                                />
                                <Select
                                    label={t('location')}
                                    value={config.google_location || 'us-central1'}
                                    data={['us-central1', 'asia-northeast3', 'europe-west1']}
                                    onChange={(v) => setConfig({ ...config, google_location: v })}
                                />
                            </Group>
                            <Textarea
                                label={t('serviceAccountJson')}
                                placeholder='{"type": "service_account", ...}'
                                minRows={3}
                                autosize
                                value={config.api_key_google || ''}
                                onChange={(e) => setConfig({ ...config, api_key_google: e.currentTarget.value })}
                            />
                        </Stack>

                        <Divider my="md" label={t('dataApis')} labelPosition="center" />

                        <Text fw={700} c="dimmed" size="sm" tt="uppercase">{t('weatherEnvironment')}</Text>
                        <TextInput
                            label={t('kmaApiKey')}
                            description={t('kmaApiKeyDesc')}
                            value={config.api_key_kma || ''}
                            onChange={(e) => setConfig({ ...config, api_key_kma: e.currentTarget.value })}
                        />
                        <TextInput
                            label={t('airKoreaApiKey')}
                            description={t('airKoreaApiKeyDesc')}
                            value={config.api_key_air || ''}
                            onChange={(e) => setConfig({ ...config, api_key_air: e.currentTarget.value })}
                        />
                    </Stack>
                </Tabs.Panel>

                <Tabs.Panel value="system" pt="md">
                    <Stack>
                        <Text fw={700}>{t('wifiSetup')}</Text>
                        <Button leftSection={<IconRefresh size={16} />} onClick={handleWifiScan} variant="outline">
                            {t('scanWifi')}
                        </Button>

                        {networks.length > 0 && (
                            <Select
                                label={t('selectNetwork')}
                                data={networks.map(n => ({ value: n.ssid, label: `${n.ssid} (${n.signal}%)` }))}
                                value={selectedWifi}
                                onChange={setSelectedWifi}
                            />
                        )}

                        {selectedWifi && (
                            <Group align="flex-end">
                                <PasswordInput
                                    label={t('password')}
                                    value={wifiPass}
                                    onChange={(e) => setWifiPass(e.currentTarget.value)}
                                    style={{ flex: 1 }}
                                />
                                <Button onClick={handleWifiConnect}>{t('connect')}</Button>
                            </Group>
                        )}

                        <Divider my="md" />
                        <Divider my="md" />
                        <Text fw={700}>{t('smartPowerTitle')}</Text>
                        <Group grow>
                            <TextInput
                                label={t('activeStartHour')}
                                description={t('activeStartDesc')}
                                type="number"
                                min={0}
                                max={23}
                                value={config.power_settings?.active_start_hour ?? 5}
                                onChange={(e) => {
                                    const val = parseInt(e.currentTarget.value) || 0;
                                    setConfig({
                                        ...config,
                                        power_settings: { ...config.power_settings, active_start_hour: val }
                                    });
                                }}
                            />
                            <TextInput
                                label={t('activeEndHour')}
                                description={t('activeEndDesc')}
                                type="number"
                                min={0}
                                max={23}
                                value={config.power_settings?.active_end_hour ?? 22}
                                onChange={(e) => {
                                    const val = parseInt(e.currentTarget.value) || 0;
                                    setConfig({
                                        ...config,
                                        power_settings: { ...config.power_settings, active_end_hour: val }
                                    });
                                }}
                            />
                        </Group>
                        <Group grow mt="xs">
                            <TextInput
                                label={t('wakeupInterval')}
                                description={t('wakeupIntervalDesc')}
                                type="number"
                                value={config.power_settings?.interval_min || 60}
                                onChange={(e) => {
                                    const val = parseInt(e.currentTarget.value) || 60;
                                    setConfig({
                                        ...config,
                                        power_settings: { ...config.power_settings, interval_min: val }
                                    });
                                }}
                            />
                            <TextInput
                                label={t('runtimeDuration')}
                                description={t('runtimeDurationDesc')}
                                type="number"
                                value={config.power_settings?.runtime_min || 3}
                                onChange={(e) => {
                                    const val = parseInt(e.currentTarget.value) || 3;
                                    setConfig({
                                        ...config,
                                        power_settings: { ...config.power_settings, runtime_min: val }
                                    });
                                }}
                            />
                        </Group>
                        <Group justify="space-between" align="center" mt="xs" p="xs" bg="gray.1" style={{ borderRadius: 8 }}>
                            <Text size="sm">{t('currentMode')}: <b>{config.power_settings?.mode?.toUpperCase() || 'SETTINGS'}</b></Text>
                            <Text size="xs" c="dimmed">
                                {config.power_settings?.mode === 'operation'
                                    ? t('modeOperation')
                                    : t('modeSettings')}
                            </Text>
                        </Group>

                        {/* Battery Estimator */}
                        <Group justify="center" mt="md" p="md" bg="blue.0" style={{ borderRadius: 8, border: '1px solid #e7f5ff' }}>
                            <Stack gap={0} align="center">
                                <Text size="sm" fw={600} c="blue.8">{t('estRuntime')}</Text>
                                <Text size="xl" fw={800} c="blue.9">
                                    {(() => {
                                        const startH = config.power_settings?.active_start_hour ?? 5;
                                        const endH = config.power_settings?.active_end_hour ?? 22;
                                        const interval = config.power_settings?.interval_min || 60;
                                        const runtime = config.power_settings?.runtime_min || 3;

                                        // Constants (Pi Zero 2W + PiSugar3)
                                        const BATTERY_CAPACITY_MAH = 5000;
                                        const EFFICIENCY = 0.9; // 90% usable
                                        const CURRENT_ACTIVE_MA = 260; // WiFi + CPU + Display
                                        const CURRENT_SLEEP_MA = 5;    // PiSugar RTC

                                        // 1. Calculate Active Hours per day
                                        let activeHours = endH - startH;
                                        if (activeHours < 0) activeHours += 24;
                                        if (activeHours === 0) activeHours = 24; // Interpret same start/end as 24h active? Or 0? Let's assume 24h if user sets 0-0. 
                                        // Actually with <24 inputs it's usually defined range.

                                        // 2. Calculate Active Minutes vs Sleep Minutes per day
                                        // Within Active Hours, we cycle: (Runtime) + (Sleep Interval)
                                        // Note: The 'interval' in my logic starts AFTER runtime.
                                        // Cycle Length = runtime + interval
                                        const cycleLength = runtime + interval;
                                        const cyclesPerActivePeriod = (activeHours * 60) / cycleLength;

                                        const dailyActiveMins = cyclesPerActivePeriod * runtime;
                                        const dailySleepMins = (24 * 60) - dailyActiveMins;

                                        // 3. Calculate Consumption
                                        const dailyConsumption_mAh =
                                            (dailyActiveMins / 60 * CURRENT_ACTIVE_MA) +
                                            (dailySleepMins / 60 * CURRENT_SLEEP_MA);

                                        // 4. Days
                                        const usableCapacity = BATTERY_CAPACITY_MAH * EFFICIENCY;
                                        const days = usableCapacity / dailyConsumption_mAh;

                                        if (days > 365) return `1 Year +`;
                                        return `${days.toFixed(1)} ${t('estDays')}`;
                                    })()}
                                </Text>
                            </Stack>
                        </Group>

                        <Text fw={700} mt="xl">{t('deviceControl')}</Text>
                        <Group>
                            <Button color="orange" onClick={() => systemAction('reboot')}>{t('reboot')}</Button>
                            <Button color="red" onClick={() => systemAction('shutdown')}>{t('shutdown')}</Button>
                            <Button color="blue" onClick={handleUpdate}>{t('update')}</Button>
                        </Group>
                    </Stack>
                </Tabs.Panel>
            </Tabs>

            <Group justify="flex-end" mt="xl">
                <Button variant="default" onClick={onClose}>{t('cancel')}</Button>
                <Button onClick={handleSave}>{t('saveChanges')}</Button>
            </Group>

            {/* update feedback modal */}
            <Modal opened={updateStatus !== 'idle'} onClose={() => { if (updateStatus !== 'loading') setUpdateStatus('idle'); }} title={t('update')} centered>
                <Stack align="center" py="lg">
                    {updateStatus === 'loading' && <Loader size="xl" />}
                    {updateStatus === 'success' && <IconCircleCheck size={50} color="green" />}
                    {updateStatus === 'uptodate' && <IconCircleCheck size={50} color="blue" />}
                    {updateStatus === 'error' && <IconAlertCircle size={50} color="red" />}

                    <Text size="lg" fw={700} mt="md">
                        {updateStatus === 'loading' && t('updateInProgress')}
                        {updateStatus === 'success' && t('updateComplete')}
                        {updateStatus === 'uptodate' && t('updateUptodate')}
                        {updateStatus === 'error' && t('updateError')}
                    </Text>

                    {updateStatus === 'success' && (
                        <Text ta="center" size="sm" c="dimmed">{t('updateDesc')}</Text>
                    )}
                    {updateStatus === 'uptodate' && (
                        <Text ta="center" size="sm" c="dimmed">{t('updateUptodateDesc')}</Text>
                    )}
                    {updateStatus === 'error' && (
                        <Text ta="center" size="sm" c="red">{updateMsg}</Text>
                    )}

                    {updateStatus !== 'loading' && (
                        <Button mt="md" fullWidth onClick={() => {
                            setUpdateStatus('idle');
                            if (updateStatus === 'success') window.location.reload();
                        }}>
                            {t('close')} {updateStatus === 'success' && `& ${t('refresh')}`}
                        </Button>
                    )}
                </Stack>
            </Modal>
        </Modal >
    );
}
