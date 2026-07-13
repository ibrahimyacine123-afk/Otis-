require('dotenv').config();
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcodeTerminal = require('qrcode-terminal');
const QRCode = require('qrcode');
const axios = require('axios');
const fs = require('fs');
const http = require('http');

// Intercepter et ignorer les erreurs de destruction de contexte Puppeteer (rechargements WhatsApp)
// Intercepter et ignorer les erreurs de destruction de contexte Puppeteer (rechargements WhatsApp)
process.on('uncaughtException', (err) => {
    if (err.message && (
        err.message.includes('Execution context was destroyed') || 
        err.message.includes('Protocol error') ||
        err.message.includes('Could not load response body') ||
        err.message.includes('EBUSY') ||
        err.message.includes('lockfile')
    )) {
        console.log('⚠️ Ignoré : Erreur Puppeteer ou système non critique (contexte, pré-vol ou verrou de fichier).');
        return;
    }
    console.error('❌ EXCEPTION CRITIQUE NON GÉRÉE :', err);
    process.exit(1);
});

// Vos numéros de téléphone autorisés (sans le +) - Ajout du numéro du bot 62225754636356 pour les tests locaux
const ALLOWED_NUMBERS = ["905411078112", "905442846826", "62225754636356"];
const FASTAPI_URL = 'http://127.0.0.1:8000/webhook';

// Cache des messages envoyés par le bot pour éviter les boucles infinies en cas d'auto-discussion
const sentMessagesCache = new Set();

const client = new Client({
    authStrategy: new LocalAuth(),
    takeoverOnConflict: true,
    takeoverTimeoutMs: 10000,
    puppeteer: {
        headless: true,
        executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
        args: [
            '--no-sandbox', 
            '--disable-setuid-sandbox',
            '--disable-session-crashed-bubble',
            '--disable-infobars',
            '--restore-last-session=false'
        ]
    }
});

client.on('qr', (qr) => {
    console.log('\n=============================================');
    console.log('📱 GÉNÉRATION DU QR CODE EN COURS...');
    console.log('=============================================\n');
    
    qrcodeTerminal.generate(qr, { small: true });
    
    // Génération en HTML auto-actualisé (évite le verrouillage de fichier Windows Photos)
    QRCode.toDataURL(qr, function (err, url) {
        if (err) throw err;
        const htmlContent = `<!DOCTYPE html>
<html>
<head>
    <title>OTIS WhatsApp Link</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            font-family: sans-serif;
            background-color: #f0f2f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        img {
            width: 280px;
            height: 280px;
        }
        h2 { color: #075e54; margin-top: 0; }
        p { color: #555; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>📱 Connecter OTIS</h2>
        <p>Ce QR Code se rafraîchit automatiquement toutes les 5 secondes.</p>
        <img src="${url}" />
        <p style="color: #999; font-size: 11px; margin-bottom: 0;">Dernière génération: ${new Date().toLocaleTimeString()}</p>
    </div>
</body>
</html>`;
        fs.writeFileSync('qr.html', htmlContent);
        console.log('✅ QR Code enregistré dans "qr.html" (Ouvre ce fichier dans ton navigateur !).');
    });
});

client.on('auth_failure', msg => {
    console.error('❌ ÉCHEC DE L\'AUTHENTIFICATION (Session expirée/corrompue) :', msg);
});

client.on('disconnected', reason => {
    console.log('❌ Client déconnecté de WhatsApp :', reason);
});

client.on('change_state', state => {
    console.log('🔄 Changement d\'état WhatsApp :', state);
});

client.on('loading_screen', (percent, message) => {
    console.log(`⏳ ÉCRAN DE CHARGEMENT : ${percent}% - ${message}`);
});

client.on('ready', () => {
    console.log('✅ Client WhatsApp connecté avec succès !');
    console.log(`🔒 Prêt à écouter les messages des numéros : ${ALLOWED_NUMBERS.join(', ')}`);
});

// Prendre une capture d'écran de débug toutes les 15 secondes pour suivre l'évolution
setInterval(async () => {
    try {
        if (client.pupPage) {
            // Activer la capture des logs de la console du navigateur s'il n'est pas déjà actif
            if (!client.pupPage._hasConsoleListener) {
                client.pupPage._hasConsoleListener = true;
                client.pupPage.on('console', msg => {
                    console.log(`🖥️ [Console Navigateur] ${msg.type().toUpperCase()}: ${msg.text()}`);
                });
            }

            // Tenter de fermer les fenêtres modales intrusives comme "Nouveautés sur WhatsApp Web" et "Utiliser ici"
            const dismissed = await client.pupPage.evaluate(() => {
                // Couvre div[role="button"] ET <button> natif (WhatsApp Web a change de markup
                // selon les versions/modales, ex: "What's new on WhatsApp Web").
                const clickables = Array.from(document.querySelectorAll('div[role="button"], button'));

                // 1. Essayer de cliquer sur le bouton "Continuer"/"Continue" (vert) ou "Use here" / "Utiliser ici"
                const greenBtn = clickables.find(b => b.textContent && (
                    b.textContent.trim() === 'Continue' ||
                    b.textContent.includes('Continuer') ||
                    b.textContent.includes('Continue') ||
                    b.textContent.includes('Use here') ||
                    b.textContent.includes('Utiliser ici') ||
                    b.textContent.includes('Utiliser dans ce navigateur')
                ));
                if (greenBtn) {
                    greenBtn.click();
                    return 'bouton Continue/Continuer';
                }

                // 2. Essayer de cliquer sur la croix de fermeture [X]
                const xIcon = document.querySelector('span[data-icon="x-light"]') || document.querySelector('span[data-icon="x"]');
                if (xIcon) {
                    const xButton = xIcon.closest('div[role="button"], button') || xIcon;
                    xButton.click();
                    return 'croix [X]';
                }

                // 3. Fallback generique : bouton de fermeture natif <button aria-label="Close">
                const closeBtn = clickables.find(b => (b.getAttribute('aria-label') || '').toLowerCase().includes('close'));
                if (closeBtn) {
                    closeBtn.click();
                    return 'bouton aria-label Close';
                }

                return null;
            });

            if (dismissed) {
                console.log(`👉 Modale fermee via : ${dismissed}`);
            } else {
                // Fallback ultime, robuste independamment du DOM : touche Echap.
                await client.pupPage.keyboard.press('Escape').catch(() => {});
            }

            await client.pupPage.screenshot({ path: 'debug_screenshot.png' });
            console.log(`📸 [${new Date().toISOString()}] Capture de débug enregistrée.`);
        }
    } catch (err) {
        console.error('❌ Erreur capture de débug/fermeture modal :', err.message);
    }
}, 15000);

client.on('message', async msg => {
    // Éviter la boucle infinie si c'est notre propre message envoyé par l'API
    if (sentMessagesCache.has(msg.body)) {
        return;
    }

    // Logger temporairement tous les messages entrants pour débugger
    const senderNumber = msg.from.split('@')[0];
    console.log(`📬 Message reçu de [${senderNumber}] (Group: ${msg.isGroupMsg || msg.from.endsWith('@g.us')}): ${msg.body}`);

    // 1. Ignorer TOUS les messages provenant de groupes
    if (msg.from.endsWith('@g.us') || msg.isGroupMsg) {
        return; // On ignore silencieusement
    }
    
    // 2. Filtrage strict : ignorer si le numéro ne correspond pas exactement
    if (!ALLOWED_NUMBERS.includes(senderNumber)) {
        console.log(`⚠️ Spam ignoré de : ${senderNumber}`);
        return; // On ignore silencieusement sans répondre
    }

    console.log(`\n📥 [WhatsApp] Message validé de ${senderNumber} : ${msg.body}`);
    
    try {
        // Transmettre le message au cerveau (FastAPI Python)
        const response = await axios.post(FASTAPI_URL, {
            message: msg.body,
            sender: senderNumber
        });

        // Récupérer la réponse du CEO et l'envoyer sur WhatsApp
        if (response.data && response.data.success) {
            console.log(`📤 [WhatsApp] Envoi de la réponse OTIS...`);
            sentMessagesCache.add(response.data.response);
            
            // Retirer du cache après 10s pour ne pas saturer
            setTimeout(() => sentMessagesCache.delete(response.data.response), 10000);
            
            await msg.reply(response.data.response);
        } else {
            console.log('❌ Réponse inattendue de l\'API Python.');
        }

    } catch (error) {
        console.error('❌ Erreur de communication avec FastAPI :', error.message);
        await msg.reply("Désolé, mon cerveau est actuellement hors ligne ou une erreur s'est produite. 🤖🔌");
    }
});

// =========================================================================
// Self-chat ("Message à toi-même") : le numero lie au bridge est le numero
// personnel du proprietaire (visible en tant que "(You)" dans la liste des
// discussions WhatsApp). whatsapp-web.js n'emet JAMAIS l'evenement 'message'
// pour les messages fromMe (envoyes par le compte lui-meme) -- y compris
// dans le self-chat -- donc tester en s'ecrivant a soi-meme ne declenchait
// jamais le webhook. 'message_create' capte aussi les messages fromMe ; on
// ne traite que ceux du self-chat (to === son propre numero) pour ne pas
// dupliquer la logique du handler 'message' ci-dessus sur les vrais contacts.
// =========================================================================
client.on('message_create', async msg => {
    if (!msg.fromMe) return;

    const selfId = client.info && client.info.wid ? client.info.wid._serialized : null;
    if (!selfId || msg.to !== selfId) return; // pas le self-chat, on laisse le handler 'message' faire son travail

    if (sentMessagesCache.has(msg.body)) return; // c'est une reponse du bot, pas une commande de l'utilisateur

    const senderNumber = selfId.split('@')[0];
    if (!ALLOWED_NUMBERS.includes(senderNumber)) return;

    console.log(`\n📥 [WhatsApp self-chat] Message validé de ${senderNumber} : ${msg.body}`);

    try {
        const response = await axios.post(FASTAPI_URL, {
            message: msg.body,
            sender: senderNumber
        });

        if (response.data && response.data.success) {
            console.log(`📤 [WhatsApp self-chat] Envoi de la réponse OTIS...`);
            sentMessagesCache.add(response.data.response);
            setTimeout(() => sentMessagesCache.delete(response.data.response), 10000);
            await client.sendMessage(selfId, response.data.response);
        } else {
            console.log('❌ Réponse inattendue de l\'API Python (self-chat).');
        }
    } catch (error) {
        console.error('❌ Erreur de communication avec FastAPI (self-chat) :', error.message);
        await client.sendMessage(selfId, "Désolé, mon cerveau est actuellement hors ligne ou une erreur s'est produite. 🤖🔌");
    }
});
// Serveur d'envoi sortant (Phase 4 : rituel matinal, messages proactifs OTIS)
// Ecoute des requetes POST /send {to, message} venant du scheduler Python.
// N'utilise que le module http natif pour eviter une dependance npm de plus.
// =========================================================================
const SEND_PORT = process.env.OTIS_BRIDGE_SEND_PORT || 8002;

const sendServer = http.createServer((req, res) => {
    if (req.method !== 'POST' || req.url !== '/send') {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: 'Route inconnue' }));
        return;
    }

    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
        try {
            const { to, message } = JSON.parse(body || '{}');

            if (!to || !message) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: false, error: "'to' et 'message' sont requis." }));
                return;
            }

            if (!ALLOWED_NUMBERS.includes(to)) {
                console.log(`⚠️ [/send] Refus d'envoi vers un numero non autorise : ${to}`);
                res.writeHead(403, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: false, error: 'Numero non autorise.' }));
                return;
            }

            const chatId = `${to}@c.us`;
            await client.sendMessage(chatId, message);
            console.log(`📤 [/send] Message proactif envoye a ${to}`);
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ success: true }));
        } catch (err) {
            console.error('❌ [/send] Erreur d\'envoi :', err.message);
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ success: false, error: err.message }));
        }
    });
});

sendServer.listen(SEND_PORT, () => {
    console.log(`📡 Serveur d'envoi OTIS actif sur le port ${SEND_PORT} (POST /send { to, message })`);
});

console.log("🚀 Initialisation du client WhatsApp...");
client.initialize();
