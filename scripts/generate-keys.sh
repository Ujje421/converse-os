#!/bin/bash
set -e

echo "Generating JWT RSA Key Pair for Converse AI Platform..."

KEYS_DIR="keys"
mkdir -p "$KEYS_DIR"

if [ -f "$KEYS_DIR/jwt-private.pem" ]; then
    echo "Keys already exist in $KEYS_DIR. Skipping."
    exit 0
fi

# Generate Private Key
openssl genpkey -algorithm RSA -out "$KEYS_DIR/jwt-private.pem" -pkeyopt rsa_keygen_bits:2048

# Extract Public Key
openssl rsa -pubout -in "$KEYS_DIR/jwt-private.pem" -out "$KEYS_DIR/jwt-public.pem"

echo "Keys generated successfully in $KEYS_DIR/"
ls -la "$KEYS_DIR"
