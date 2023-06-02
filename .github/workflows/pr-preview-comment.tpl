**A preview of your PR is ready to use.✅**

Huma Platform Play API links:

- [⚕️ Clinician Portal]({{ .url }})
- [👨‍🔧📝📋 API docs]({{ .url }}/apidocs/)
- [👨‍🔧📏📝📊 Grafana dashboard with PPserver logs]({{ .dashboard_url }})
- [💓 back-end health status]({{ .url }}/health/ready)
- [⚙️ back-end version]({{ .url }}/version)

Client information links:

- [📱 iOS QR code]({{ .url }}/api/public/v1beta/region?clientId=c1&type=qrCode)
- [🤖 Android QR code]({{ .url }}/api/public/v1beta/region?clientId=c2&type=qrCode)
- [⚕️ CP]({{ .url }}/api/public/v1beta/region?clientId=c3)

⛁ You can access your MongoDB using:

- web, [mongo-express]({{ .url }}/mongo-express/)
  For basic auth please use the username​​👨‍💻​ `{{ .username }}` and the password🔑: `{{ .password }}`.
- shell, run in a shell `mongosh {{ .mongo_host }}:27017/{{ .username }} -u {{ .username }}`
  and provide the password🔑: `{{ .password }}` in a prompt.

🪣 The S3 bucket url is `s3://{{ .bucket }}`.
You can access this S3 bucket using profile "huma-sandbox" in [AWS Console](https://s3.console.aws.amazon.com/s3/buckets/{{ .bucket }}?region={{ .region }}).
To access it the same way as `huma-server-sdk` please use following static credentials:

```sh
AWS_ACCESS_KEY_ID=`{{ .id }}`
AWS_SECRET_ACCESS_KEY=`{{ .secret }}`
AWS_DEFAULT_REGION=`{{ .region }}`
```
