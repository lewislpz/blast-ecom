export default {
  input: '../backend/openapi.yaml',
  output: 'src/shared/api/generated',
  plugins: ['@hey-api/typescript'],
}
