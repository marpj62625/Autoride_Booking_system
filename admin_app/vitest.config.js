import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.test.js'],
    reporters: ['verbose'],
    globals: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['**/*.js'],
      exclude: [
        'node_modules/**',
        'tests/**',
        'vitest.config.js',
        'validate-*.js',
        'test-*.html'
      ]
    }
  }
});
