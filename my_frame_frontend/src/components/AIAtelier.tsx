import { useState, useEffect } from 'react';
import { Card, Text, Select, TextInput, Button, Group, Image, Stack, Loader } from '@mantine/core';
import { IconWand } from '@tabler/icons-react';
import { generateAI, getPhotoUrl, getConfig, saveConfig } from '../api';

interface AIAtelierProps {
    onImageGenerated: () => void; // call to reload gallery
}

export function AIAtelier({ onImageGenerated }: AIAtelierProps) {
    const [prompt, setPrompt] = useState('');
    const [style, setStyle] = useState('anime style');
    const [provider, setProvider] = useState('huggingface');
    const [generating, setGenerating] = useState(false);
    const [lastImage, setLastImage] = useState<string | null>(null);

    useEffect(() => {
        // Load saved provider
        getConfig().then(cfg => {
            if (cfg.ai_provider) setProvider(cfg.ai_provider);
        });
    }, []);

    const handleProviderChange = (val: string | null) => {
        if (!val) return;
        setProvider(val);
        saveConfig({ ai_provider: val }); // Auto-save preference
    };

    const handleGenerate = async () => {
        if (!prompt) return;
        setGenerating(true);
        try {
            const res = await generateAI(prompt, style);
            if (res.status === 'success' && res.image) {
                setLastImage(res.image);
                onImageGenerated();
            }
        } catch (e) {
            alert("Generation failed");
        } finally {
            setGenerating(false);
        }
    };

    return (
        <Card shadow="sm" radius="md" withBorder>
            <Stack gap="md">
                <Group justify="space-between">
                    <Text fw={700} size="lg">AI Atelier 🎨</Text>
                    <Select
                        data={[
                            { value: 'huggingface', label: 'HuggingFace (Free)' },
                            { value: 'google', label: 'Google Vertex AI' }
                        ]}
                        value={provider}
                        onChange={handleProviderChange}
                        size="xs"
                        w={150}
                        allowDeselect={false}
                    />
                </Group>

                <TextInput
                    placeholder="E.g. A cat sitting on a windowsill"
                    label="Prompt"
                    value={prompt}
                    onChange={(e) => setPrompt(e.currentTarget.value)}
                />

                <Select
                    label="Art Style"
                    value={style}
                    onChange={(v) => setStyle(v || 'anime style')}
                    data={[
                        { value: 'anime style', label: 'Ghibli Anime' },
                        { value: 'photorealistic', label: 'Photorealistic' },
                        { value: 'oil painting', label: 'Oil Painting' },
                        { value: 'watercolor', label: 'Watercolor' },
                        { value: 'cyberpunk', label: 'Cyberpunk' },
                        { value: 'pixel art', label: 'Pixel Art' },
                        { value: 'lego', label: 'Lego' },
                    ]}
                />

                <Button
                    onClick={handleGenerate}
                    loading={generating}
                    disabled={!prompt}
                    fullWidth
                    variant="gradient"
                    gradient={{ from: 'indigo', to: 'cyan' }}
                    leftSection={<IconWand size={16} />}
                >
                    Generate Artwork
                </Button>

                {lastImage && (
                    <Stack align="center" mt="sm">
                        <Text size="sm" c="dimmed">Last Generated Result</Text>
                        <Image
                            src={getPhotoUrl(lastImage)}
                            radius="md"
                            h={200}
                            w="auto"
                            fit="contain"
                        />
                    </Stack>
                )}
            </Stack>
        </Card>
    );
}
