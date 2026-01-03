import { useState, useEffect } from 'react';
import { AppShell, Container, Grid, Title, Group, Button, Select, Badge, Tooltip } from '@mantine/core';
import { IconPhoto, IconSettings, IconBattery, IconBatteryCharging, IconBattery1, IconBattery2, IconBattery3, IconBattery4 } from '@tabler/icons-react';

import { PreviewCard } from './components/PreviewCard';
import { Gallery } from './components/Gallery';
import { AIAtelier } from './components/AIAtelier';
import { SettingsModal } from './components/SettingsModal';
import { saveConfig, getConfig, getBatteryStatus } from './api';
import { LanguageProvider, useLanguage } from './context/LanguageContext';
import type { Language } from './translations';

function BatteryStatus() {
  const [battery, setBattery] = useState<{ level: number; charging: boolean } | null>(null);

  useEffect(() => {
    const fetchBat = async () => {
      try {
        const status = await getBatteryStatus();
        setBattery(status);
      } catch (e) {
        console.error("Battery fetch failed", e);
      }
    };

    fetchBat();
    const interval = setInterval(fetchBat, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, []);

  if (!battery) return null;

  // Determine Icon
  let Icon = IconBattery;
  if (battery.charging) Icon = IconBatteryCharging;
  else if (battery.level < 20) Icon = IconBattery1;
  else if (battery.level < 50) Icon = IconBattery2;
  else if (battery.level < 80) Icon = IconBattery3;
  else Icon = IconBattery4;

  const color = battery.level < 20 && !battery.charging ? 'red' : 'green';

  return (
    <Tooltip label={`Battery: ${battery.level}%${battery.charging ? ' (Charging)' : ''}`}>
      <Group gap={4} mr="xs">
        <Icon size={20} color={color} />
        <Badge variant="light" color={color} size="sm">{Math.round(battery.level)}%</Badge>
      </Group>
    </Tooltip>
  );
}

function MainApp() {
  const { t, language, setLanguage } = useLanguage();
  const [selectedPhoto, setSelectedPhoto] = useState<string>('');
  const [shuffleMode, setShuffleMode] = useState(false);
  const [shufflePlaylist, setShufflePlaylist] = useState<string[]>([]);
  const [powerMode, setPowerMode] = useState<string>('settings');

  const [refreshPreview, setRefreshPreview] = useState(0);
  const [settingsOpen, setSettingsOpen] = useState(false);

  // Sync state with backend config on load
  useEffect(() => {
    getConfig().then(cfg => {
      if (cfg.selected_photo) setSelectedPhoto(cfg.selected_photo);
      if (cfg.shuffle_mode !== undefined) setShuffleMode(cfg.shuffle_mode);
      if (cfg.shuffle_playlist) setShufflePlaylist(cfg.shuffle_playlist);
      if (cfg.power_settings?.mode) setPowerMode(cfg.power_settings.mode);
    });
  }, []);

  const handlePhotoSelect = async (photo: string) => {
    setSelectedPhoto(photo);
    // If selecting a specific photo, we might want to disable shuffle automatically? 
    // Or just let backend logic handle it (Backend prioritizes shuffle if enabled).
    // Let's force shuffle OFF if user explicitly picks a single photo for clarity.
    if (shuffleMode) {
      setShuffleMode(false);
      await saveConfig({ selected_photo: photo, shuffle_mode: false });
    } else {
      await saveConfig({ selected_photo: photo });
    }

    // Refresh preview to show selected photo
    setTimeout(() => setRefreshPreview(prev => prev + 1), 300);
  };

  const handleToggleShuffle = async (enabled: boolean) => {
    setShuffleMode(enabled);
    await saveConfig({ shuffle_mode: enabled }, false); // Don't refresh preview immediately, maybe?
    // Actually, if enabled, preview should update to random. 
    setTimeout(() => setRefreshPreview(prev => prev + 1), 300);
  };

  const handleUpdatePlaylist = async (playlist: string[]) => {
    setShufflePlaylist(playlist);
    await saveConfig({ shuffle_playlist: playlist }, false);
  };

  const handleAIComplete = () => {
    setRefreshPreview(prev => prev + 1);
    window.location.reload();
  };

  return (
    <>
      <AppShell
        header={{ height: 60 }}
        padding="md"
        style={{ background: '#f5f5f7' }}
      >
        <AppShell.Header
          style={{
            background: 'rgba(255,255,255,0.7)',
            backdropFilter: 'blur(20px)',
            borderBottom: '1px solid rgba(0,0,0,0.05)'
          }}
        >
          <Container size="xl" h="100%">
            <Group h="100%" align="center" justify="space-between">
              <Group>
                <IconPhoto size={28} color="#007AFF" />
                <Title order={3} style={{ fontWeight: 600 }}>{t('appTitle')}</Title>
              </Group>

              {/* Desktop Menu */}
              <Group visibleFrom="sm">
                {/* Battery Status */}
                <BatteryStatus />

                <Select
                  data={[
                    { value: 'ko', label: '🇰🇷 한국어' },
                    { value: 'en', label: '🇺🇸 English' },
                    { value: 'ja', label: '🇯🇵 日本語' },
                    { value: 'zh', label: '🇨🇳 中文' },
                  ]}
                  value={language}
                  onChange={(v) => setLanguage(v as Language)}
                  w={120}
                  size="xs"
                  radius="md"
                  allowDeselect={false}
                />
                <Button variant="default" radius="xl" leftSection={<IconSettings size={18} />} onClick={() => setSettingsOpen(true)}>
                  {t('settings')}
                </Button>
                {/* Mode Indicator */}
                <Badge
                  variant="dot"
                  color={powerMode === 'operation' ? 'green' : 'orange'}
                  size="lg"
                >
                  {powerMode === 'operation' ? 'AUTO MODE' : 'MANUAL'}
                </Badge>
              </Group>

              {/* Mobile Menu Button */}
              <Group hiddenFrom="sm">
                <Button variant="subtle" size="sm" p={0} onClick={() => setSettingsOpen(true)}>
                  <IconSettings size={24} />
                </Button>
              </Group>
            </Group>
          </Container>
        </AppShell.Header>

        <AppShell.Main>
          <Container size="xl">
            <Grid gutter="xl">
              {/* Left Column: Preview */}
              <Grid.Col span={{ base: 12, md: 5 }}>
                <PreviewCard refreshKey={refreshPreview} selectedPhoto={selectedPhoto} />
              </Grid.Col>

              {/* Right Column: Controls */}
              <Grid.Col span={{ base: 12, md: 7 }}>
                <Grid gutter="md">
                  <Grid.Col span={12}>
                    <AIAtelier onImageGenerated={handleAIComplete} />
                  </Grid.Col>
                  <Grid.Col span={12}>
                    <Gallery
                      selectedPhoto={selectedPhoto}
                      onSelectPhoto={handlePhotoSelect}
                      // [Shuffle Props]
                      shuffleMode={shuffleMode}
                      shufflePlaylist={shufflePlaylist}
                      onToggleShuffle={handleToggleShuffle}
                      onUpdatePlaylist={handleUpdatePlaylist}
                    />
                  </Grid.Col>
                </Grid>
              </Grid.Col>
            </Grid>
          </Container>
        </AppShell.Main>
      </AppShell>
      <SettingsModal opened={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  );
}

export default function App() {
  return (
    <LanguageProvider>
      <MainApp />
    </LanguageProvider>
  );
}

