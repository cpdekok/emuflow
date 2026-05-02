package com.emuflow.agent.ui

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Environment
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import androidx.navigation.compose.rememberNavController
import com.emuflow.agent.BuildConfig
import com.emuflow.agent.R
import com.emuflow.agent.cleanslate.VendorShellManager
import com.emuflow.agent.telemetry.DeviceIdManager
import com.emuflow.agent.ui.theme.EmuFlowAgentTheme

private const val PREFS_SETTINGS = "emuflow_settings"
private const val KEY_TELEMETRY_ENABLED = "telemetry_enabled"

/**
 * SettingsScreen — telemetrie opt-out, vault-map, clean-slate en over-informatie.
 *
 * Secties:
 * 1. Privacy — telemetrie opt-out toggle
 * 2. Save Vault — vault-locatie, handmatige backup
 * 3. Clean-slate — vendor-packages disablen/herstellen
 * 4. Over — versie-informatie, backend-URL
 */
@Composable
fun SettingsScreen(navController: NavController) {
    val context = LocalContext.current
    val prefs = context.getSharedPreferences(PREFS_SETTINGS, Context.MODE_PRIVATE)
    var telemetryEnabled by remember {
        mutableStateOf(prefs.getBoolean(KEY_TELEMETRY_ENABLED, true))
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text(
            text = stringResource(R.string.settings_title),
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold
        )

        // Sectie 1: Privacy
        PrivacySection(
            telemetryEnabled = telemetryEnabled,
            onTelemetryToggle = { enabled ->
                telemetryEnabled = enabled
                prefs.edit().putBoolean(KEY_TELEMETRY_ENABLED, enabled).apply()
            }
        )

        // Sectie 2: Save Vault
        SaveVaultSection(context = context)

        // Sectie 3: Clean-slate
        CleanSlateSection(context = context)

        // Sectie 4: Over
        AboutSection()
    }
}

@Composable
private fun PrivacySection(
    telemetryEnabled: Boolean,
    onTelemetryToggle: (Boolean) -> Unit
) {
    val context = LocalContext.current

    SettingsCard(title = stringResource(R.string.settings_privacy_title)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = stringResource(R.string.settings_telemetry_label),
                    style = MaterialTheme.typography.bodyLarge
                )
                Text(
                    text = stringResource(R.string.settings_telemetry_desc),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                )
            }
            Switch(
                checked = telemetryEnabled,
                onCheckedChange = onTelemetryToggle
            )
        }

        HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))

        // Wettelijke disclaimer (doc 11 — tekst uit Legal-advies)
        Text(
            text = stringResource(R.string.settings_legal_disclaimer),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f)
        )
    }
}

@Composable
private fun SaveVaultSection(context: Context) {
    SettingsCard(title = stringResource(R.string.settings_vault_title)) {
        Text(
            text = stringResource(R.string.settings_vault_location),
            style = MaterialTheme.typography.bodyMedium
        )
        Text(
            text = "${Environment.getExternalStorageDirectory().absolutePath}/EmuFlow_Vault/",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.primary
        )

        OutlinedButton(
            onClick = {
                // Open bestandsbeheerder op vault-locatie (doc 11)
                val vaultUri = Uri.parse(
                    "content://com.android.externalstorage.documents/root/primary"
                )
                val intent = Intent(Intent.ACTION_VIEW, vaultUri).apply {
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK
                }
                try {
                    context.startActivity(intent)
                } catch (e: Exception) {
                    // Bestandsbeheerder niet beschikbaar — geen actie
                }
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(stringResource(R.string.settings_vault_open))
        }
    }
}

@Composable
private fun CleanSlateSection(context: Context) {
    var cleanSlateRunning by remember { mutableStateOf(false) }
    var lastResult by remember { mutableStateOf<String?>(null) }

    SettingsCard(title = stringResource(R.string.settings_cleanslate_title)) {
        Text(
            text = stringResource(R.string.settings_cleanslate_desc),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
        )

        Button(
            onClick = {
                // STUB: In fase 2 uitvoeren via coroutine met Shizuku-check
                val results = VendorShellManager.runCleanSlate(context)
                lastResult = if (results.isEmpty()) {
                    "Geen vendor-packages gevonden op dit device"
                } else {
                    results.joinToString("\n") { "${it.packageName}: ${it.message}" }
                }
            },
            modifier = Modifier.fillMaxWidth(),
            enabled = !cleanSlateRunning
        ) {
            Text(stringResource(R.string.settings_cleanslate_run))
        }

        OutlinedButton(
            onClick = {
                val results = VendorShellManager.runRestore(context)
                lastResult = if (results.isEmpty()) {
                    "Geen vendor-packages om te herstellen"
                } else {
                    results.joinToString("\n") { "${it.packageName}: ${it.message}" }
                }
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(stringResource(R.string.settings_cleanslate_restore))
        }

        lastResult?.let { result ->
            Text(
                text = result,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.secondary
            )
        }
    }
}

@Composable
private fun AboutSection() {
    val context = LocalContext.current
    val deviceId = DeviceIdManager.getCurrentDeviceId(context)

    SettingsCard(title = stringResource(R.string.settings_about_title)) {
        SettingsInfoRow(
            label = stringResource(R.string.settings_about_version),
            value = BuildConfig.AGENT_VERSION
        )
        SettingsInfoRow(
            label = stringResource(R.string.settings_about_backend),
            value = BuildConfig.BACKEND_URL
        )
        SettingsInfoRow(
            label = stringResource(R.string.settings_about_device_id),
            value = deviceId?.take(8)?.let { "$it…" } ?: "—"
        )
    }
}

@Composable
private fun SettingsCard(title: String, content: @Composable ColumnScope.() -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.secondary
            )
            content()
        }
    }
}

@Composable
private fun SettingsInfoRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
            modifier = Modifier.weight(1f)
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodySmall,
            modifier = Modifier.weight(1f)
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun SettingsScreenPreview() {
    EmuFlowAgentTheme {
        SettingsScreen(navController = rememberNavController())
    }
}
