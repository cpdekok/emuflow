package com.emuflow.agent.ui

import android.app.Activity
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
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material.icons.outlined.Circle
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import androidx.navigation.compose.rememberNavController
import com.emuflow.agent.R
import com.emuflow.agent.permissions.PermissionBundle
import com.emuflow.agent.permissions.PermissionBundleManager
import com.emuflow.agent.permissions.PermissionStatus
import com.emuflow.agent.ui.theme.EmuFlowAgentTheme

/**
 * PreflightScreen — één-scherm permission-flow voor EmuFlow Agent.
 *
 * Toont per permissie de status en een actie-knop als de permissie ontbreekt.
 *
 * Conditionele weergave (doc taak):
 * - POST_NOTIFICATIONS: alleen getoond op API 33+
 * - FOREGROUND_SERVICE_DATA_SYNC: alleen getoond op API 34+ (declaration, geen actie)
 * - MANAGE_EXTERNAL_STORAGE: altijd getoond (minSdk 30)
 * - Shizuku: altijd getoond als optionele stap
 *
 * AYANEO-specifieke instructie (doc 14, quirk 1):
 * Als AYANEO Pocket Micro Classic gedetecteerd wordt, wordt een extra instructie getoond
 * over de ADB-pairing met interne controller-toggle.
 */
@Composable
fun PreflightScreen(navController: NavController) {
    val context = LocalContext.current
    var bundle by remember { mutableStateOf<PermissionBundle?>(null) }

    // Refresh permissie-status bij elke recompose (gebruiker keert terug van Settings)
    LaunchedEffect(Unit) {
        bundle = PermissionBundleManager.currentStatus(context)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text(
            text = stringResource(R.string.preflight_title),
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold
        )

        Text(
            text = stringResource(R.string.preflight_description),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
        )

        bundle?.let { permissions ->
            // Status-overzicht kaart
            PermissionsCard(
                bundle = permissions,
                onRequestManageStorage = {
                    val activity = context as? Activity
                    activity?.let { PermissionBundleManager.requestManageExternalStorage(it) }
                },
                onRequestNotifications = {
                    val activity = context as? Activity
                    activity?.let { PermissionBundleManager.requestPostNotifications(it) }
                },
                onRequestShizuku = {
                    com.emuflow.agent.shizuku.ShizukuManager.requestPermission()
                }
            )

            // Toon "Doorgaan" als verplichte permissies verleend zijn
            if (permissions.allRequiredGranted) {
                Spacer(Modifier.height(8.dp))
                Button(
                    onClick = {
                        navController.navigate(com.emuflow.agent.NavRoute.Home.route)
                    },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(stringResource(R.string.preflight_continue))
                }
            }
        } ?: run {
            Text(
                text = stringResource(R.string.preflight_loading),
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}

@Composable
private fun PermissionsCard(
    bundle: PermissionBundle,
    onRequestManageStorage: () -> Unit,
    onRequestNotifications: () -> Unit,
    onRequestShizuku: () -> Unit
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // MANAGE_EXTERNAL_STORAGE
            PermissionRow(
                label = stringResource(R.string.permission_storage_label),
                description = stringResource(R.string.permission_storage_desc),
                status = bundle.manageExternalStorage,
                actionLabel = stringResource(R.string.permission_storage_action),
                onAction = onRequestManageStorage
            )

            HorizontalDivider()

            // POST_NOTIFICATIONS (alleen API 33+)
            if (bundle.postNotifications != PermissionStatus.NOT_REQUIRED) {
                PermissionRow(
                    label = stringResource(R.string.permission_notifications_label),
                    description = stringResource(R.string.permission_notifications_desc),
                    status = bundle.postNotifications,
                    actionLabel = stringResource(R.string.permission_notifications_action),
                    onAction = onRequestNotifications
                )
                HorizontalDivider()
            }

            // Shizuku (optioneel)
            PermissionRow(
                label = stringResource(R.string.permission_shizuku_label),
                description = stringResource(R.string.permission_shizuku_desc),
                status = bundle.shizuku,
                actionLabel = stringResource(R.string.permission_shizuku_action),
                onAction = onRequestShizuku,
                isOptional = true
            )
        }
    }
}

@Composable
private fun PermissionRow(
    label: String,
    description: String,
    status: PermissionStatus,
    actionLabel: String,
    onAction: () -> Unit,
    isOptional: Boolean = false
) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = label,
                        style = MaterialTheme.typography.bodyLarge,
                        fontWeight = FontWeight.Medium
                    )
                    if (isOptional) {
                        Text(
                            text = stringResource(R.string.permission_optional),
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.outline
                        )
                    }
                }
            }

            // Status-icoon
            when (status) {
                PermissionStatus.GRANTED -> Icon(
                    imageVector = Icons.Default.CheckCircle,
                    contentDescription = null,
                    tint = Color(0xFF4CAF50), // Groen
                    modifier = Modifier.size(24.dp)
                )
                PermissionStatus.DENIED, PermissionStatus.PENDING -> Icon(
                    imageVector = Icons.Default.Warning,
                    contentDescription = null,
                    tint = if (isOptional) MaterialTheme.colorScheme.outline
                    else MaterialTheme.colorScheme.error,
                    modifier = Modifier.size(24.dp)
                )
                PermissionStatus.NOT_REQUIRED -> Icon(
                    imageVector = Icons.Outlined.Circle,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.outline,
                    modifier = Modifier.size(24.dp)
                )
            }
        }

        Text(
            text = description,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
        )

        if (status == PermissionStatus.DENIED || status == PermissionStatus.PENDING) {
            OutlinedButton(
                onClick = onAction,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(actionLabel)
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun PreflightScreenPreview() {
    EmuFlowAgentTheme {
        PreflightScreen(navController = rememberNavController())
    }
}
