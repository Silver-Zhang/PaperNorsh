"use client";

import { PreferencesForm } from "@/components/preferences/preferences-form";

export default function SettingsPage() {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-zinc-900">Settings</h2>
        <p className="text-zinc-500 text-sm mt-1">
          Configure your paper preferences and delivery settings.
        </p>
      </div>
      <PreferencesForm />
    </div>
  );
}
