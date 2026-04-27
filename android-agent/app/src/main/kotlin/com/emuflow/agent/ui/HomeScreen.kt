package com.emuflow.agent.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
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
import com.emuflow.agent.NavRoute
import com.emuflow.agent.R
import com.emuflow.agent.hardware.HardwareProfile
import com.emuflow.agent.hardware.detectHardwareProfile
import com.emuflow.agent.ui.theme.EmuFlowAgentTheme
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * HomeScreen — status-overzicht en Resume Last Game.
 *
 * Toont:
 * - Hardware-status (device-naam, SoC, controller-layout)
 * - Heartbeat-status (actief / inactief)
 * - Save Vault status (laatste backup-tijd)
 * - "Verder spelen" knop (Resume Last Game — stub in fase 1)
 *
 * Design: Material 3, minimalistisch, geen animaties in fase 1.
 */
@Composable
fun HomeScreen(navController: NavController) {
    val context = LocalContext.current
    var hardwareProfile by remember { mutableStateOf<HardwareProfile?>(null) }

    // Detecteer hardware-profiel asynchroon (I/O-bound)
    LaunchedEffect(Unit) {
        hardwareProfile = withContext(Dispatchers.IO) {
            detectHardwareProfile(context)
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // App-titel
        Text(
            text = stringResource(R.string.app_name),
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary
        )

        // Resume Last Game knop (fase 1 stub)
        ResumeLastGameCard(navController = navController)

        // Hardware-status card
        hardwareProfile?.let { profile ->
            HardwareStatusCard(profile = profile)
        }

        // Service-status card
        ServiceStatusCard()

        // Save Vault status card
        SaveVaultStatusCard()
    }
}

/**
 * Kaart voor "Verder spelen" / Resume Last Game (doc 11).
 *
 * Fase 1 STUB: knop is zichtbaar maar ontkoppeld van emulator-launch.
 * In fase 2: koppelen aan ActivityManager voor laatste emulator-process detectie.
 */
@Composable
private fun ResumeLastGameCard(navController: NavController) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = stringResource(R.string.home_resume_title),
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold
            )
            Text(
                text = stringResource(R.string.home_resume_no_game),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
            )
            Button(
                onClick = {
                    // STUB: Fase 2 — start laatste emulator met laatste game
                },
                modifier = Modifier.fillMaxWidth(),
                enabled = false // Uitgeschakeld totdat "laatste game" bekend is
            ) {
                Icon(
                    imageVector = Icons.Default.PlayArrow,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(Modifier.size(8.dp))
                Text(stringResource(R.string.home_resume_button))
            }
        }
    }
}

/**
 * Kaart met hardware-profiel samenvatting.
 */
@Composable
private fun HardwareStatusCard(profile: HardwareProfile) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = stringResource(R.string.home_hardware_title),
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.secondary
            )
            StatusRow(
                label = stringResource(R.string.home_hardware_device),
                value = "${profile.manufacturer} ${profile.model}"
            )
            StatusRow(
                label = stringResource(R.string.home_hardware_soc),
                value = profile.socChip
            )
            StatusRow(
                label = stringResource(R.string.home_hardware_android),
                value = "Android ${profile.androidRelease} (API ${profile.androidApi})"
            )
            StatusRow(
                label = stringResource(R.string.home_hardware_controller),
                value = profile.controllerLayout
            )
            StatusRow(
                label = stringResource(R.string.home_hardware_ram),
                value = "${profile.ramMb} MB"
            )
        }
    }
}

/**
 * Kaart met service-status (HeartbeatService, SaveWatcherService).
 */
@Composable
private fun ServiceStatusCard() {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = stringResource(R.string.home_services_title),
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.secondary
            )
            // STUB: In fase 2 koppelen aan service-status via ServiceConnection of StateFlow
            StatusRow(
                label = stringResource(R.string.home_service_heartbeat),
                value = stringResource(R.string.status_stub)
            )
            StatusRow(
                label = stringResource(R.string.home_service_save_watcher),
                value = stringResource(R.string.status_stub)
            )
        }
    }
}

/**
 * Kaart met Save Vault status.
 */
@Composable
private fun SaveVaultStatusCard() {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = stringResource(R.string.home_vault_title),
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.secondary
            )
            StatusRow(
                label = stringResource(R.string.home_vault_last_backup),
                value = stringResource(R.string.home_vault_no_backup_yet)
            )
            StatusRow(
                label = stringResource(R.string.home_vault_size),
                value = "—"
            )
        }
    }
}

/**
 * Herbruikbare label-waarde rij.
 */
@Composable
private fun StatusRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
            modifier = Modifier.weight(1f)
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Medium,
            modifier = Modifier.weight(1f)
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun HomeScreenPreview() {
    EmuFlowAgentTheme {
        HomeScreen(navController = rememberNavController())
    }
}
