import { useState, useEffect } from 'react';
import { Card, Text, Select, TextInput, Button, Group, Image, Stack, Checkbox } from '@mantine/core';
import { IconWand } from '@tabler/icons-react';
import { generateAI, getPhotoUrl, getConfig, saveConfig, fetchPhotos } from '../api';
import { useLanguage } from '../context/LanguageContext';

interface AIAtelierProps {
    onImageGenerated: () => void;
}

// Fun & Rich Style Presets
const STYLES = [
    { value: 'no_style', label: '🚫 화풍 없음 (No Style)' },
    { value: 'Watercolor', label: '🎨 수채화 (Watercolor)' },
    { value: 'Oil Painting, Van Gogh style', label: '🌻 유화 (반 고흐 스타일)' },
    { value: 'Studio Ghibli', label: '🍃 지브리 애니메이션' },
    { value: 'Pixel Art', label: '👾 픽셀 아트' },
    { value: 'Lego Brick', label: '🧱 레고 블록' },
    { value: 'Claymation', label: '🥣 클레이 애니메이션' },
    { value: 'Origami', label: '📄 종이접기' },
    { value: 'Cyberpunk', label: '🌃 사이버펑크' },
    { value: 'Makoto Shinkai', label: '🌠 신카이 마코토 (초고화질)' },
    { value: 'Polaroid', label: '📸 폴라로이드 사진' },
    { value: '3D Cute Character Rendering', label: '🧸 3D 귀여운 캐릭터' },
    { value: 'Steampunk', label: '⚙️ 스팀펑크' },
    { value: 'Pencil Sketch', label: '✏️ 연필 스케치' },
    { value: 'Futuristic City', label: '🚀 미래도시' },
    { value: 'Vintage Comic Book', label: '📖 옛날 만화책' },
];

export function AIAtelier({ onImageGenerated }: AIAtelierProps) {
    const { t } = useLanguage();
    const [prompt, setPrompt] = useState('');
    const [style, setStyle] = useState('Watercolor'); // Default to first item
    const [provider, setProvider] = useState('huggingface');
    const [loading, setLoading] = useState(false);
    const [lastImage, setLastImage] = useState<string | null>(null);

    // Multimodal State
    const [useImage, setUseImage] = useState(false);
    const [availablePhotos, setAvailablePhotos] = useState<string[]>([]);
    const [selectedInputImages, setSelectedInputImages] = useState<string[]>([]);

    useEffect(() => {
        getConfig().then(cfg => {
            if (cfg.ai_provider) setProvider(cfg.ai_provider);
        });

        // Load photos for selector
        fetchPhotos().then(photos => {
            setAvailablePhotos(photos);
            // Dont auto select for multi-mode, let user choose
        });
    }, []);

    const handleChangeProvider = async (val: string) => {
        setProvider(val);
        await saveConfig({ ai_provider: val });
    };

    const handleGenerate = async () => {
        setLoading(true);
        try {
            const imagesToUse = (useImage && provider === 'google') ? selectedInputImages : undefined;
            const res = await generateAI(prompt, style, imagesToUse);
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
                        { value: 'google', label: 'Google Gemini (Nano Banana) 🍌' },
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
                    label="화풍 선택 / Style Select"
                    value={style}
                    onChange={(v) => setStyle(v as string)}
                    data={STYLES}
                    searchable
                    maxDropdownHeight={280}
                />



                {provider === 'google' && (
                    <Card withBorder p="xs" radius="sm" style={{ backgroundColor: '#f8f9fa' }}>
                        <Group justify="space-between" mb="xs">
                            <Text size="sm" fw={500}>🖼️ 이미지와 함께 전송 (Multimodal)</Text>
                            <Checkbox
                                checked={useImage}
                                onChange={(e) => setUseImage(e.currentTarget.checked)}
                            />
                        </Group>

                        {useImage && (
                            <Stack mt="xs">
                                <Text size="xs" c="dimmed">
                                    선택된 이미지: {selectedInputImages.length}장
                                </Text>
                                <div style={{
                                    display: 'grid',
                                    gridTemplateColumns: 'repeat(4, 1fr)',
                                    gap: '8px',
                                    maxHeight: '200px',
                                    overflowY: 'auto',
                                    padding: '4px'
                                }}>
                                    {availablePhotos.map((photo) => {
                                        const isSelected = selectedInputImages.includes(photo);
                                        return (
                                            <div
                                                key={photo}
                                                onClick={() => {
                                                    setSelectedInputImages(prev =>
                                                        isSelected
                                                            ? prev.filter(p => p !== photo)
                                                            : [...prev, photo]
                                                    );
                                                }}
                                                style={{
                                                    cursor: 'pointer',
                                                    border: isSelected ? '3px solid #228be6' : '1px solid #ddd',
                                                    borderRadius: '8px',
                                                    overflow: 'hidden',
                                                    position: 'relative',
                                                    aspectRatio: '1'
                                                }}
                                            >
                                                <Image
                                                    src={getPhotoUrl(photo)}
                                                    w="100%"
                                                    h="100%"
                                                    fit="cover"
                                                />
                                                {isSelected && (
                                                    <div style={{
                                                        position: 'absolute',
                                                        top: 0, right: 0, left: 0, bottom: 0,
                                                        background: 'rgba(34, 139, 230, 0.3)',
                                                        display: 'flex',
                                                        justifyContent: 'center',
                                                        alignItems: 'center'
                                                    }}>
                                                        <Text size="xl">✔️</Text>
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            </Stack>
                        )}
                    </Card>
                )}

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
