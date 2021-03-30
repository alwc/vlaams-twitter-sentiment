output "https_certificate" {
  value = aws_acm_certificate_validation.https_certificate.certificate_arn
}
