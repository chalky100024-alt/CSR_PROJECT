import { useState, useEffect } from 'react';
import { Card, Text, Select, TextInput, Button, Group, Image, Stack } from '@mantine/core';
import { IconWand } from '@tabler/icons-react';
import { generateAI, getPhotoUrl, getConfig, saveConfig } from '../api';
import { useLanguage } from '../context/LanguageContext';

interface AIAtelierProps {
    onImageGenerated: () => void;
}

export function AIAtelier({ onImageGenerated }: AIAtelierProps) {
    const { t } = useLanguage();
    const [prompt, setPrompt] = useState('');
    const [style, setStyle] = useState('anime style');
    const [provider, setProvider] = useState('huggingface');
    const [loading, setLoading] = useState(false);
    const [lastImage, setLastImage] = useState<string | null>(null);

    useEffect(() => {
        getConfig().then(cfg => {
            if (cfg.ai_provider) setProvider(cfg.ai_provider);
        });
    }, []);

    const handleChangeProvider = async (val: string) => {
        setProvider(val);
        await saveConfig({ ai_provider: val });
    };

    const handleGenerate = async () => {
        setLoading(true);
        try {
            const res = await generateAI(prompt, style);
            if (res.status === 'success') {
                if (res.image) setLastImage(res.image);
                onImageGenerated();
            } else {
                alert("Generation failed");
            }
        } catch (e) {
            alert("Error generating image");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card shadow="sm" radius="md" withBorder>
            <Group justify="space-between" mb="sm">
                <Group>
                    <IconWand size={20} color="purple" />
                    <Text fw={700} size="lg">{t('aiTitle')}</Text>
                </Group>
                <Select
                    size="xs"
                    value={provider}
                    onChange={(v) => handleChangeProvider(v as string)}
                    data={[
                        { value: 'huggingface', label: 'HuggingFace (Free)' },
                        { value: 'google', label: 'Google Vertex AI (High Quality)' },
                    ]}
                    allowDeselect={false}
                />
            </Group>

            <Stack>
                <TextInput
                    placeholder={t('aiPromptPlaceholder')}
                    value={prompt}
                    onChange={(e) => setPrompt(e.currentTarget.value)}
                />

                <Select
                    value={style}
                    onChange={(v) => setStyle(v as string)}
                    data={[
                        { value: 'anime style', label: 'Studio Ghibli' },
                        { value: 'photorealistic', label: 'Photorealistic' },
                        { value: 'oil painting', label: 'Van Gogh Oil' },
                        { value: 'watercolor', label: 'Watercolor' },
                        { value: 'lego', label: 'Lego' }
                    ]}
                />

                <Button
                    fullWidth
                    variant="gradient"
                    gradient={{ from: 'indigo', to: 'cyan' }}
                    onClick={handleGenerate}
                    loading={loading}
                >
                    {loading ? t('generating') : t('generateBtn')}
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
