import { useState, useEffect } from 'react';
import {
    Modal, Tabs, TextInput, Button, Group, Stack, Text,
    Select, PasswordInput, ScrollArea, Textarea, Divider
} from '@mantine/core';
import { IconMapPin, IconKey, IconDeviceDesktop, IconRefresh } from '@tabler/icons-react';
import { getConfig, saveConfig, searchLocation, scanWifi, connectWifi, systemAction } from '../api';

interface SettingsModalProps {
    opened: boolean;
    onClose: () => void;
}

export function SettingsModal({ opened, onClose }: SettingsModalProps) {
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
        alert("Settings Saved!");
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
            alert("Scan failed");
        }
    };

    const handleWifiConnect = async () => {
        if (!selectedWifi) return;
        await connectWifi(selectedWifi, wifiPass);
        alert("Connection attempt sent!");
    };

    return (
        <Modal opened={opened} onClose={onClose} title="Settings ⚙️" size="lg">
            <Tabs value={activeTab} onChange={setActiveTab}>
                <Tabs.List>
                    <Tabs.Tab value="general" leftSection={<IconMapPin size={14} />}>General</Tabs.Tab>
                    <Tabs.Tab value="api" leftSection={<IconKey size={14} />}>API Keys</Tabs.Tab>
                    <Tabs.Tab value="system" leftSection={<IconDeviceDesktop size={14} />}>System</Tabs.Tab>
                </Tabs.List>

                <Tabs.Panel value="general" pt="md">
                    <Stack>
                        <TextInput
                            label="Current Location"
                            value={config.location?.name || 'Not Set'}
                            readOnly
                            rightSection={<IconMapPin size={16} />}
                        />

                        <Group align="flex-end">
                            <TextInput
                                label="Search Location (Korean)"
                                placeholder="e.g. 고덕"
                                value={locQuery}
                                onChange={(e) => setLocQuery(e.currentTarget.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSearchLoc()}
                                style={{ flex: 1 }}
                            />
                            <Button onClick={handleSearchLoc}>Search</Button>
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
                        <Text fw={700} c="dimmed" size="sm" tt="uppercase">Image Generation</Text>

                        <Group align="flex-start" grow>
                            <TextInput
                                label="HuggingFace API Token"
                                placeholder="hf_..."
                                value={config.api_key_hf || ''}
                                onChange={(e) => setConfig({ ...config, api_key_hf: e.currentTarget.value })}
                            />
                        </Group>

                        <Stack gap="xs" mt="sm">
                            <Text size="sm" fw={500}>Google Vertex AI</Text>
                            <Group grow>
                                <TextInput
                                    label="Project ID"
                                    placeholder="my-project-id"
                                    value={config.google_project_id || ''}
                                    onChange={(e) => setConfig({ ...config, google_project_id: e.currentTarget.value })}
                                />
                                <Select
                                    label="Location"
                                    value={config.google_location || 'us-central1'}
                                    data={['us-central1', 'asia-northeast3', 'europe-west1']}
                                    onChange={(v) => setConfig({ ...config, google_location: v })}
                                />
                            </Group>
                            <Textarea
                                label="Service Account JSON (Key)"
                                placeholder='{"type": "service_account", ...}'
                                minRows={3}
                                autosize
                                value={config.api_key_google || ''}
                                onChange={(e) => setConfig({ ...config, api_key_google: e.currentTarget.value })}
                            />
                        </Stack>

                        <Divider my="md" label="Data APIs" labelPosition="center" />

                        <Text fw={700} c="dimmed" size="sm" tt="uppercase">Weather & Environment</Text>
                        <TextInput
                            label="KMA Weather API Key (Encoding)"
                            description="기상청 공공데이터포털 일반 인증키 (Decoding이 아닌 Encoding 키 사용 권장)"
                            value={config.api_key_kma || ''}
                            onChange={(e) => setConfig({ ...config, api_key_kma: e.currentTarget.value })}
                        />
                        <TextInput
                            label="AirKorea Dust API Key"
                            description="한국환경공단 에어코리아 대기오염정보"
                            value={config.api_key_air || ''}
                            onChange={(e) => setConfig({ ...config, api_key_air: e.currentTarget.value })}
                        />
                    </Stack>
                </Tabs.Panel>

                <Tabs.Panel value="system" pt="md">
                    <Stack>
                        <Text fw={700}>Wi-Fi Setup</Text>
                        <Button leftSection={<IconRefresh size={16} />} onClick={handleWifiScan} variant="outline">
                            Scan Networks
                        </Button>

                        {networks.length > 0 && (
                            <Select
                                label="Select Network"
                                data={networks.map(n => ({ value: n.ssid, label: `${n.ssid} (${n.signal}%)` }))}
                                value={selectedWifi}
                                onChange={setSelectedWifi}
                            />
                        )}

                        {selectedWifi && (
                            <Group align="flex-end">
                                <PasswordInput
                                    label="Password"
                                    value={wifiPass}
                                    onChange={(e) => setWifiPass(e.currentTarget.value)}
                                    style={{ flex: 1 }}
                                />
                                <Button onClick={handleWifiConnect}>Connect</Button>
                            </Group>
                        )}

                        <Text fw={700} mt="xl">Device Control</Text>
                        <Group>
                            <Button color="orange" onClick={() => systemAction('reboot')}>Reboot</Button>
                            <Button color="red" onClick={() => systemAction('shutdown')}>Shutdown</Button>
                            <Button color="blue" onClick={() => systemAction('update')}>Git Pull Update</Button>
                        </Group>
                    </Stack>
                </Tabs.Panel>
            </Tabs>

            <Group justify="flex-end" mt="xl">
                <Button variant="default" onClick={onClose}>Cancel</Button>
                <Button onClick={handleSave}>Save Changes</Button>
            </Group>
        </Modal>
    );
}
