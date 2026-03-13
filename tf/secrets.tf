resource "aws_secretsmanager_secret" "twilio" {
  name = "parking-permit-bot/twilio"

  tags = {
    ManagedBy = "terraform"
  }
}
