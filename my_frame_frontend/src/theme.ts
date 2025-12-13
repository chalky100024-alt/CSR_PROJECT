import { createTheme, rem } from '@mantine/core';

export const theme = createTheme({
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"',
    headings: {
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
        fontWeight: '600',
    },

    // Apple Colors
    colors: {
        // Custom blue scale based on Apple's #007AFF
        appleBlue: [
            '#eef7ff', '#d9e9ff', '#b3d0ff', '#8ab6ff', '#669fff',
            '#4d90fe', '#007aff', '#0066cc', '#0052a3', '#003d7a'
        ],
    },
    primaryColor: 'appleBlue',
    primaryShade: 6,

    // Global Radius (Apple uses fairly large rounding)
    defaultRadius: 'md', // 8px default, we can override to lg (12px) for cards

    // Components Defaults
    components: {
        Button: {
            defaultProps: {
                radius: 'xl', // Capsule buttons
                fw: 500,
            },
        },
        Card: {
            defaultProps: {
                radius: 'lg',
                padding: 'lg',
                withBorder: true,
            },
            styles: (theme) => ({
                root: {
                    backgroundColor: 'rgba(255, 255, 255, 0.8)', // Semi-transparent
                    backdropFilter: 'blur(20px)', // Glassmorphism
                    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)', // Soft shadow
                    transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                    '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: '0 8px 30px rgba(0, 0, 0, 0.08)',
                    }
                }
            })
        },
        TextInput: {
            defaultProps: {
                radius: 'md',
                size: 'md',
            },
            styles: {
                input: {
                    backgroundColor: 'rgba(245, 245, 247, 0.8)', // Apple Light Gray #F5F5F7
                    border: '1px solid transparent',
                    '&:focus': {
                        backgroundColor: '#fff',
                        borderColor: '#007AFF',
                    }
                }
            }
        },
        Select: {
            defaultProps: {
                radius: 'md',
                size: 'md',
            },
            styles: {
                input: {
                    backgroundColor: 'rgba(245, 245, 247, 0.8)',
                    border: '1px solid transparent',
                    '&:focus': {
                        backgroundColor: '#fff',
                    }
                }
            }
        }
    },
});
