% LOG_EXTRA_SIGNALS  Re-run copies of the models with To Workspace blocks for signals that were
% not saved in the scope figures: VDS (Voltage Measurement2), VGS (PWM output), Vo, Iin and,
% in the closed-loop models, the PI controller output (duty ratio).
%
% The models in models/ are copied to build/sim/ first, so the originals are never changed.
% Output: data/sim/<model>_sim.mat with a struct R.<signal>.t / R.<signal>.y

root   = fileparts(fileparts(fileparts(mfilename('fullpath'))));
work   = fullfile(root, 'build', 'sim');
outdir = fullfile(root, 'data', 'sim');
if ~exist(work, 'dir'), mkdir(work); end
if ~exist(outdir, 'dir'), mkdir(outdir); end

names = {'research_paper', 'research_paper_cmrcc', ...
         'research_paper_closed_loop', 'research_paper_closed_loop_load_step'};
for k = 1:numel(names)
    n = names{k};
    copyfile(fullfile(root, 'models', [n '.slx']), fullfile(work, [n '.slx']));
    load_system(fullfile(work, [n '.slx']));
    logs = {'Voltage Measurement2', 'VDS'; 'PWM Generator', 'VGS'; ...
            'Voltage Measurement1', 'Vo';  'Current Measurement', 'Iin'};
    if ~isempty(find_system(n, 'SearchDepth', 1, 'Name', 'PID Controller'))
        logs(end+1, :) = {'PID Controller', 'Duty'};
    end
    for j = 1:size(logs, 1)
        add_block('simulink/Sinks/To Workspace', [n '/TW_' logs{j,2}], ...
                  'VariableName', logs{j,2}, 'SaveFormat', 'Timeseries');
        add_line(n, [logs{j,1} '/1'], ['TW_' logs{j,2} '/1']);
    end
    set_param(n, 'ReturnWorkspaceOutputs', 'on');
    out = sim(n);
    R = struct();
    for j = 1:size(logs, 1)
        ts = out.get(logs{j,2});
        R.(logs{j,2}).t = ts.Time;
        R.(logs{j,2}).y = squeeze(ts.Data);
    end
    save(fullfile(outdir, [n '_sim.mat']), 'R', '-v7');
    close_system(n, 0);
    fprintf('%s simulated\n', n);
end
