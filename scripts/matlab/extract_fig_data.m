% EXTRACT_FIG_DATA  Convert the Simulink scope figures (*.fig) into compact .mat files.
% The scope figures ("Print to Figure") store each trace as a Stair object with ~1e6 samples
% at the 50 ns solver step. They are 20-480 MB each and are therefore not kept in the repository.
%
% Usage: place the .fig files in data/scope_figs/ and run this script from the repository root.
% Output: data/fig_data/<figure name>.mat, each holding a struct array S with fields
%         name (signal label), t0, dt, n, y (single), panel/axes positions and axis limits.

root   = fileparts(fileparts(fileparts(mfilename('fullpath'))));
src    = fullfile(root, 'data', 'scope_figs');
outdir = fullfile(root, 'data', 'fig_data');
if ~exist(outdir, 'dir'), mkdir(outdir); end

d = dir(fullfile(src, '*.fig'));
[~, ix] = sort([d.bytes]); d = d(ix);
for k = 1:numel(d)
    nm = d(k).name(1:end-4);
    if exist(fullfile(outdir, [nm '.mat']), 'file'), continue; end
    f  = openfig(fullfile(src, d(k).name), 'invisible');
    ax = findall(f, 'Type', 'axes');
    S  = struct('name', {}, 'panelpos', {}, 'axpos', {}, 'xlim', {}, 'ylim', {}, ...
                't0', {}, 'dt', {}, 'n', {}, 'maxdtdev', {}, 'y', {}, 'color', {});
    c = 0;
    for i = 1:numel(ax)
        L = findall(ax(i), 'Type', 'stair');
        pp = [0 0 1 1];
        try, pp = getpixelposition(ax(i).Parent, true); catch, end
        for j = 1:numel(L)
            c = c + 1; x = L(j).XData; dx = diff(x);
            S(c).name = L(j).DisplayName;   S(c).panelpos = pp;
            S(c).axpos = getpixelposition(ax(i), true);
            S(c).xlim = ax(i).XLim;  S(c).ylim = ax(i).YLim;  S(c).color = L(j).Color;
            S(c).t0 = x(1);  S(c).dt = median(dx);  S(c).n = numel(x);
            S(c).maxdtdev = max(abs(dx - S(c).dt));
            S(c).y = single(L(j).YData);
        end
    end
    save(fullfile(outdir, [nm '.mat']), 'S', '-v7');
    close(f);
    fprintf('%s done\n', nm);
end
