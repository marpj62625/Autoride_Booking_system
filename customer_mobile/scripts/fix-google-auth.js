const fs = require('fs');
const path = require('path');

const buildGradlePath = path.join(__dirname, '..', 'node_modules', '@codetrix-studio', 'capacitor-google-auth', 'android', 'build.gradle');

if (fs.existsSync(buildGradlePath)) {
  let content = fs.readFileSync(buildGradlePath, 'utf8');
  
  // Replace jcenter() with mavenCentral()
  content = content.replace(/jcenter\(\)/g, 'mavenCentral()');
  
  fs.writeFileSync(buildGradlePath, content, 'utf8');
  console.log('? Fixed Google Auth plugin build.gradle (replaced jcenter with mavenCentral)');
} else {
  console.log('??  Google Auth plugin build.gradle not found');
}
