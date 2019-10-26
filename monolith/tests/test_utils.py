from monolith.app import create_app

def client():
    #aggiungere tutte le configurazioni richieste
    app = create_app()
    return app.test_client()

#funzionalità che vengono richieste per testare tutte le altre#
def login(client, email, password):
    return client.post('/login', data=dict(email=email, password=password))


def logout(client):
    return client.get('/logout')