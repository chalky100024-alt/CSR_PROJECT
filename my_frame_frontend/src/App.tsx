import { useState } from 'react';
import { AppShell, Container, Grid, Title, Group, Button, Select } from '@mantine/core';
import { IconPhoto, IconSettings } from '@tabler/icons-react';

import { PreviewCard } from './components/PreviewCard';
import { Gallery } from './components/Gallery';
import { AIAtelier } from './components/AIAtelier';
import { SettingsModal } from './components/SettingsModal';
import { saveConfig } from './api';
import { LanguageProvider, useLanguage } from './context/LanguageContext';
import type { Language } from './translations';

function MainApp() {
  const { t, language, setLanguage } = useLanguage();
  const [selectedPhoto, setSelectedPhoto] = useState<string>('');
  const [refreshPreview, setRefreshPreview] = useState(0);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const handlePhotoSelect = async (photo: string) => {
    setSelectedPhoto(photo);
    // Auto-select photo on backend
    await saveConfig({ selected_photo: photo }, false);
    // Refresh preview to show selected photo
    setTimeout(() => setRefreshPreview(prev => prev + 1), 300);
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
              <Group>
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

