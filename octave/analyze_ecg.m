pkg load biosig signal tsa;

Fs = 1000
Fnyq = Fs/2

f = "../scripts/edf_1628463711.edf";

clear ecg_raw ecg_filt arspec_raw arspec_filt b a ecg_filt_bp;

ecg_raw = sload(f, [1 2 3]);
[ecg_filt, header] = remove5060hz(f, "NOTCH"); # cannot specify channels
ecg_filt = ecg_filt(:, 1:3);

arspec_raw = arspectrum(ecg_raw, 1000, 4256+19);
arspec_filt = arspectrum(ecg_filt, 1000, 4256+19);

# plota(arspec_filt);
# plot(ecg_filt);

Fcl = 0.5;
Fch = 250;

[b, a] = butter(5, [Fcl/Fnyq, Fch/Fnyq]);
ecg_filt_bp = filtfilt(b, a, ecg_filt);

t = "";

for i = 1:size(ecg_filt_bp, 2)
   subplot(size(ecg_filt_bp, 2), 1, i)
   plot(ecg_filt_bp(5000:15000, i))
   t = [t, "I"];
   title(t)
   grid on;
   xlabel("t/ms")
   ylabel("V/µV")
end
