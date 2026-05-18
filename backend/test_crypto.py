from crypto import (
    derive_key,
    encrypt_document,
    decrypt_document,
    generate_trapdoor
)


def test_encrypt_decrypt():
    key = derive_key("password123")
    text = "Kidney failure test document"
    encrypted = encrypt_document(key, text)
    decrypted = decrypt_document(key, encrypted)

    assert decrypted == text
    print("Encryption/Decryption test passed")


def test_trapdoor_consistency():
    key1 = derive_key("password123")
    key2 = derive_key("password123")
    key3 = derive_key("different")

    trigram = "kid"

    t1 = generate_trapdoor(key1, trigram)
    t2 = generate_trapdoor(key2, trigram)
    t3 = generate_trapdoor(key3, trigram)

    assert t1 == t2
    assert t1 != t3

    print("Trapdoor consistency test passed")


if __name__ == "__main__":
    test_encrypt_decrypt()
    test_trapdoor_consistency()