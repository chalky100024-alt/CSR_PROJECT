import { useState } from 'react';
import { AppShell, Container, Grid, Title, Text, Group, Button } from '@mantine/core';
import { IconPhoto, IconSettings } from '@tabler/icons-react';

import { PreviewCard } from './components/PreviewCard';
import { Gallery } from './components/Gallery';
import { AIAtelier } from './components/AIAtelier';
import { SettingsModal } from './components/SettingsModal';
import { saveConfig } from './api';

function App() {
  const [selectedPhoto, setSelectedPhoto] = useState<string>('');
  const [refreshPreview, setRefreshPreview] = useState(0);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const handlePhotoSelect = async (photo: string) => {
    setSelectedPhoto(photo);
    // Auto-select photo on backend
    await saveConfig({ selected_photo: photo }, false);
    // Refresh preview to show selected photo
    setTimeout(() => setRefreshPreview(prev => prev + 1), 500);
  };

  const handleAIComplete = () => {
    // Reload gallery (handled inside Gallery via key or ref matching? 
    // Actually Gallery reloads on mount, but we need to trigger it. 
    // Ideally use React Query, but simpler: Force App refresh or pass signal)
    // For now, we mainly need preview to update if AI set it as background
    setRefreshPreview(prev => prev + 1);
    // We will rely on Gallery auto-refresh or user manual refresh for now to keep it simple
    // Or we can lift 'photos' state up. But let's just trigger preview for result.
    window.location.reload(); // Brute force refresh for Gallery to catch up (simplest for MVP)
  };

  return (
    <>
      <AppShell
        header={{ height: 60 }}
        padding="md"
        style={{ background: '#f5f5f7' }} // Apple background gray
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
                <Title order={3} style={{ fontWeight: 600 }}>MyFrame Studio</Title>
              </Group>
              <Button variant="default" radius="xl" leftSection={<IconSettings size={18} />} onClick={() => setSettingsOpen(true)}>
                Settings
              </Button>
            </Group>
          </Container>
        </AppShell.Header>

        <AppShell.Main>
          <Container size="xl">
            <Grid gutter="xl">
              {/* Left Column: Preview (Sticky on Desktop potentially) */}
              <Grid.Col span={{ base: 12, md: 5 }}>
                <PreviewCard refreshKey={refreshPreview} />
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

export default App;
