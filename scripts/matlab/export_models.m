% EXPORT_MODELS  Export each Simulink model's diagram (PNG) and block parameters (TXT).
% Run from the repository root in MATLAB R2024b (Simscape Electrical / Specialized Power Systems).
% Outputs go to build/models/. The original .slx files are not modified.

root   = fileparts(fileparts(fileparts(mfilename('fullpath'))));
outdir = fullfile(root, 'build', 'models');
if ~exist(outdir, 'dir'), mkdir(outdir); end

names = {'research_paper', 'research_paper_cmrcc', ...
         'research_paper_closed_loop', 'research_paper_closed_loop_load_step'};

for k = 1:numel(names)
    n = names{k};
    load_system(fullfile(root, 'models', [n '.slx']));

    fid = fopen(fullfile(outdir, [n '_params.txt']), 'w');
    fprintf(fid, 'MODEL %s\nSolver=%s StopTime=%s\n', n, get_param(n, 'Solver'), get_param(n, 'StopTime'));
    blks = find_system(n, 'LookUnderMasks', 'none', 'FollowLinks', 'on', 'Type', 'Block');
    for b = 1:numel(blks)
        bh = blks{b};
        try, mt = get_param(bh, 'MaskType'); catch, mt = ''; end
        fprintf(fid, '\n## %s | %s | %s\n', bh, get_param(bh, 'BlockType'), mt);
        try
            f = fieldnames(get_param(bh, 'DialogParameters'));
            for j = 1:numel(f)
                v = get_param(bh, f{j});
                if ischar(v) && numel(v) < 200, fprintf(fid, '   %s = %s\n', f{j}, v); end
            end
        catch
        end
    end
    fclose(fid);

    set_param(n, 'ZoomFactor', 'FitSystem');
    print(['-s' n], '-dpng', '-r300', fullfile(outdir, [n '_diagram.png']));
    close_system(n, 0);
end
disp('Model export done.');
