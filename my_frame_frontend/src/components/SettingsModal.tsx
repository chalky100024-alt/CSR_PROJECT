import { useState, useEffect } from 'react';
import {
    Modal, Tabs, TextInput, Button, Group, Stack, Text,
    Select, PasswordInput, ScrollArea, Textarea, Divider
} from '@mantine/core';
import { IconMapPin, IconKey, IconDeviceDesktop, IconRefresh } from '@tabler/icons-react';
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

                        <Group align="flex-end">
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
                                mb="md"
                            />

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

                        <Text fw={700} mt="xl">{t('deviceControl')}</Text>
                        <Group>
                            <Button color="orange" onClick={() => systemAction('reboot')}>{t('reboot')}</Button>
                            <Button color="red" onClick={() => systemAction('shutdown')}>{t('shutdown')}</Button>
                            <Button color="blue" onClick={() => systemAction('update')}>{t('update')}</Button>
                        </Group>
                    </Stack>
                </Tabs.Panel>
            </Tabs>

            <Group justify="flex-end" mt="xl">
                <Button variant="default" onClick={onClose}>{t('cancel')}</Button>
                <Button onClick={handleSave}>{t('saveChanges')}</Button>
            </Group>
        </Modal>
    );
}
